import os
import random
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import numpy as np
import pygame
import torch

from game.config import SIMPLE_HILL, SceneConfig, build_agents
from game.interface import ACTION_NAMES, GameInterface
from rl.dqn import DQNPopulation, ReplayBuffer, get_device
from rl.observations import (OBSERVATION_LABELS, OBSERVATION_SIZE,
                             build_observations)
from rl.sandbox import SandboxState, TrainingSandbox

# ---------------------------------------------------------------------------
# Training parameters (edit here)
# ---------------------------------------------------------------------------
CONFIG = {
    "seed": 0,
    "num_agents": 5,
    "hidden": 5,
    "device": "auto",                 # "auto" | "cuda" | "cpu"
    "learning_rate": 1e-2,
    "gamma": 0.99,
    "batch_size": 64,
    "replay_capacity": 20000,
    "min_replay": 1000,
    "train_every": 2,                 # learn once every N decisions
    "target_update": 500,             # learn steps between target copies
    "grad_clip": 10.0,                # gradient norm clipping (0 = off)
    "reward_scale": 100.0,            # scales rewards so TD targets are O(1)
    "frame_skip": 4,                  # act once every N game frames
    # Exploration (epsilon-greedy)
    "epsilon_start": 1.0,
    "epsilon_end": 0.15,
    "epsilon_decay_steps": 1500,
    "epsilon_reset_per_generation": False,
    # Evolution
    "replace_fraction": 0.5,          # worst fraction replaced by best copy
    "mutation_prob": 0.10,            # per-weight mutation probability
    "mutation_std": 0.05,             # gaussian noise std
    # Reward
    "time_penalty": 0.05,             # per SECOND without scoring
    "death_penalty": 4.0,             # must exceed max time_penalty accrual
    "lava_penalty": 6.0,              # when death cause is lava
    "miss_penalty": 0.02,             # per punch that hits nobody
    "approach_scale": 0.5,            # shaping: get closer to the flag
    "zone_reward": 0.2,               # per second standing in the flag zone
    "obs_horizon": 30.0,             # seconds used to normalize time
    # Episode / generation
    "max_generation_seconds": 60.0,
    # Rendering / sandbox
    "render": True,
    "fps": 60,
    # Persistence
    "best_dir": "best_weights",
    "checkpoint_dir": "checkpoints",
    "save_checkpoint": True,
    "save_best": True,
}


def epsilon_for(step: int, cfg: dict) -> float:
    decay = cfg["epsilon_decay_steps"]
    frac = min(1.0, step / decay) if decay > 0 else 1.0
    return cfg["epsilon_end"] + (cfg["epsilon_start"] - cfg["epsilon_end"]) * \
        (1.0 - frac)


def display_activations(activations, index: int):
    obs, h1, h2, q = activations

    def normalize(values):
        magnitudes = np.abs(np.asarray(values, dtype=float))
        peak = magnitudes.max()
        if peak < 1e-9:
            return magnitudes
        return np.clip(magnitudes / peak, 0.0, 1.0)

    inputs = np.clip(np.abs(obs[index]), 0.0, 1.0)
    return [inputs.tolist(), normalize(h1[index]).tolist(),
            normalize(h2[index]).tolist(), normalize(q[index]).tolist()]


def main() -> None:
    cfg = dict(CONFIG)
    if os.environ.get("AOTH_HEADLESS"):
        cfg["render"] = False
    if os.environ.get("AOTH_AGENTS"):
        cfg["num_agents"] = int(os.environ["AOTH_AGENTS"])
    if os.environ.get("AOTH_GEN_SECONDS"):
        cfg["max_generation_seconds"] = float(
            os.environ["AOTH_GEN_SECONDS"])
    debug = bool(os.environ.get("AOTH_DEBUG"))

    seed = cfg["seed"]
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    pygame.init()
    scene = SceneConfig(level=SIMPLE_HILL,
                        agents=build_agents(cfg["num_agents"], seed))
    env = GameInterface(scene)
    device = get_device(cfg["device"])
    count = env.num_agents
    action_count = env.action_space_size

    pop = DQNPopulation(count, OBSERVATION_SIZE, cfg["hidden"], action_count,
                        cfg["learning_rate"], device, seed)
    replay = ReplayBuffer(count, cfg["replay_capacity"], OBSERVATION_SIZE,
                          device)

    os.makedirs(cfg["best_dir"], exist_ok=True)
    os.makedirs(cfg["checkpoint_dir"], exist_ok=True)

    sandbox = None
    screen = None
    clock = None
    if cfg["render"]:
        network_layers = [OBSERVATION_SIZE, cfg["hidden"], cfg["hidden"],
                          action_count]
        sandbox = TrainingSandbox(
            games=[env],
            game_size=(scene.window.width, scene.window.height),
            supersample=scene.supersample,
            network_layers=network_layers,
            network_draw=network_layers,
            title="KotH - DQN",
        )
        screen = pygame.display.set_mode((sandbox.width, sandbox.height),
                                         vsync=1)
        pygame.display.set_caption("AI of the Hill - DQN Training")
        clock = pygame.time.Clock()

    generation = 1
    global_decisions = 0
    best_record = -1
    history = []
    running = True

    while running:
        env.reset(seed=seed + generation)
        obs_np = build_observations(env.world, env.agents, cfg["obs_horizon"])
        obs = torch.tensor(obs_np, device=device)
        prev_scores = torch.tensor([p.score for p in env.agents],
                                   dtype=torch.float32, device=device)
        prev_alive = torch.tensor([p.alive for p in env.agents],
                                  dtype=torch.bool, device=device)
        prev_missed = torch.tensor([p.missed_punches for p in env.agents],
                                   dtype=torch.float32, device=device)

        frame = 0
        decision_in_gen = 0
        gen_elapsed = 0.0
        loss_value = 0.0
        actions = torch.zeros(count, dtype=torch.long, device=device)

        while (running and not env.world.game_over
               and gen_elapsed < cfg["max_generation_seconds"]):
            if cfg["render"]:
                dt = min(clock.tick(cfg["fps"]) / 1000.0, 0.05)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key == pygame.K_t:
                            env.world.show_sensors = \
                                not env.world.show_sensors
            else:
                dt = 1.0 / cfg["fps"]
            gen_elapsed += dt

            step_in_skip = frame % cfg["frame_skip"]
            if step_in_skip == 0:
                step = (decision_in_gen if cfg["epsilon_reset_per_generation"]
                        else global_decisions)
                epsilon = epsilon_for(step, cfg)
                actions = pop.act(obs, epsilon)

            env.step([env.action_from_index(int(a)) for a in actions])
            frame += 1
            if debug and frame % 3000 == 0:
                print(f"  frame {frame} t={env.world.time:.1f} "
                      f"alive={sum(p.alive for p in env.agents)} "
                      f"decisions={decision_in_gen}", flush=True)

            if step_in_skip == cfg["frame_skip"] - 1:
                new_scores = torch.tensor([p.score for p in env.agents],
                                          dtype=torch.float32, device=device)
                new_alive = torch.tensor([p.alive for p in env.agents],
                                         dtype=torch.bool, device=device)
                new_obs = torch.tensor(
                    build_observations(env.world, env.agents,
                                       cfg["obs_horizon"]), device=device)
                delta = new_scores - prev_scores
                died = prev_alive & ~new_alive
                penalty = torch.zeros(count, device=device)
                for i in range(count):
                    if bool(died[i]):
                        cause = env.agents[i].death_cause
                        penalty[i] = (cfg["lava_penalty"] if cause == "lava"
                                      else cfg["death_penalty"])
                missed = torch.tensor(
                    [p.missed_punches for p in env.agents],
                    dtype=torch.float32, device=device)
                miss_delta = missed - prev_missed
                prev_missed = missed
                step_seconds = cfg["frame_skip"] / cfg["fps"]
                approach = cfg["approach_scale"] * (obs[:, 1] - new_obs[:, 1])
                zone = torch.tensor(
                    [1.0 if p.alive and p.in_zone(
                        env.world.flag_x, env.world.zone_half,
                        env.world.flag_ground_y, env.world.zone_height)
                     else 0.0 for p in env.agents],
                    dtype=torch.float32, device=device)
                reward = (delta
                          - cfg["time_penalty"] * (delta == 0).float()
                          * step_seconds
                          - penalty
                          - cfg["miss_penalty"] * miss_delta
                          + approach
                          + cfg["zone_reward"] * step_seconds * zone)
                reward = reward * cfg["reward_scale"]
                done = (~new_alive).float()
                replay.push(obs, actions, reward, new_obs, done)
                prev_scores, prev_alive = new_scores, new_alive
                obs = new_obs
                if (replay.size >= cfg["min_replay"] and
                        decision_in_gen % cfg["train_every"] == 0):
                    loss_value = pop.train(
                        *replay.sample(cfg["batch_size"]),
                        gamma=cfg["gamma"],
                        target_update=cfg["target_update"],
                        grad_clip=cfg["grad_clip"])
                decision_in_gen += 1
                global_decisions += 1

            if cfg["render"]:
                order = sorted(
                    range(count),
                    key=lambda i: (env.agents[i].score,
                                   env.agents[i].alive),
                    reverse=True)
                best_index = order[0]
                ranking = [
                    {"name": env.agents[i].name, "color": env.agents[i].color,
                     "score": env.agents[i].score,
                     "alive": env.agents[i].alive}
                    for i in order[:8]
                ]
                activations = pop.layer_activations(obs)
                network = display_activations(activations, best_index)
                state = SandboxState(
                    generation=generation,
                    population=count,
                    alive=sum(1 for p in env.agents if p.alive),
                    record=env.agents[best_index].score,
                    title=f"eps {epsilon:.2f}   loss {loss_value:.3f}",
                    network=network,
                    best=env.agents[best_index],
                    ranking=ranking,
                    input_labels=OBSERVATION_LABELS,
                    output_labels=ACTION_NAMES,
                    input_values=activations[0][best_index].tolist(),
                    output_values=activations[3][best_index].tolist(),
                    history=history,
                )
                sandbox.draw(screen, state, dt)
                pygame.display.flip()

        if not running:
            break

        if cfg["save_checkpoint"]:
            torch.save(
                {"generation": generation, "state": pop.state_dict()},
                os.path.join(cfg["checkpoint_dir"], f"gen_{generation:04d}.pt"))
        scores = torch.tensor([p.score for p in env.agents],
                              dtype=torch.float32, device=device)
        gen_best_index = int(torch.argmax(scores).item())
        gen_best_score = int(scores.max().item())
        history.append((generation, gen_best_score))
        if cfg["save_best"] and gen_best_score > best_record:
            best_record = gen_best_score
            torch.save(
                {"generation": generation, "agent": gen_best_index,
                 "score": gen_best_score,
                 "weights": pop.agent_weights(gen_best_index)},
                os.path.join(cfg["best_dir"], "best.pt"))

        pop.evolve(scores, cfg["replace_fraction"],
                   cfg["mutation_prob"], cfg["mutation_std"])
        print(f"generation {generation} done | best agent {gen_best_index} "
              f"score {gen_best_score} | record {best_record} | "
              f"decisions {decision_in_gen}", flush=True)
        generation += 1

    pygame.quit()


if __name__ == "__main__":
    main()
