import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
import torch

from game.config import SIMPLE_HILL, SceneConfig, build_agents
from game.hud import HUD
from game.interface import GameInterface
from game.world import AgentAction
from rl.dqn import SingleAgentDQN, get_device
from rl.observations import OBSERVATION_SIZE, build_observations

DEMO_AGENTS = 5
FRAME_SKIP = 4
OBS_HORIZON = 30.0
BEST_PATH = os.path.join(_ROOT, "best_weights", "best.pt")


def player_action(keys) -> AgentAction:
    return AgentAction(
        move=int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) -
        int(keys[pygame.K_LEFT] or keys[pygame.K_a]),
        jump=bool(keys[pygame.K_UP] or keys[pygame.K_w]),
        punch=bool(keys[pygame.K_SPACE] or keys[pygame.K_j] or
                  keys[pygame.K_f]),
        use_item=bool(keys[pygame.K_e]),
    )


def main() -> None:
    if not os.path.exists(BEST_PATH):
        print(f"trained weights not found: {BEST_PATH}")
        print("run 'bash run.sh train' first to generate best.pt")
        return

    scene = SceneConfig(level=SIMPLE_HILL, agents=build_agents(DEMO_AGENTS))
    window = scene.window
    pygame.init()
    screen = pygame.display.set_mode((window.width, window.height), vsync=1)
    pygame.display.set_caption("AI of the Hill - You vs trained AI")
    clock = pygame.time.Clock()

    env = GameInterface(scene)
    hud = HUD(scene)
    policy = SingleAgentDQN.load(BEST_PATH, get_device("auto"))
    if policy.w["W1"].shape[1] != OBSERVATION_SIZE:
        print(f"best.pt expects {policy.w['W1'].shape[1]} inputs but the game "
              f"now uses {OBSERVATION_SIZE}; retrain with 'bash run.sh train'")
        return
    supersample = max(1, scene.supersample)
    buffer = pygame.Surface(
        (window.width * supersample, window.height * supersample))
    frame = pygame.Surface((window.width, window.height))

    env.reset()
    hero = env.world.controllables[0]
    ai_indices = [i for i, a in enumerate(env.agents) if a is not hero]
    ai_actions = [0] * len(ai_indices)
    frame_count = 0

    running = True
    while running:
        dt = min(clock.tick(window.fps) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    env.reset()
                    hero = env.world.controllables[0]
                    ai_indices = [i for i, a in enumerate(env.agents)
                                  if a is not hero]
                    ai_actions = [0] * len(ai_indices)

        obs = torch.tensor(
            build_observations(env.world, env.agents, OBS_HORIZON),
            device=policy.device)
        if frame_count % FRAME_SKIP == 0:
            q_actions = policy.act(obs)
            ai_actions = [int(q_actions[i]) for i in ai_indices]

        actions = {hero: player_action(pygame.key.get_pressed())}
        for idx, agent in enumerate([env.agents[i] for i in ai_indices]):
            actions[agent] = env.action_from_index(ai_actions[idx])
        env.step(actions)
        frame_count += 1

        buffer.fill(window.background)
        env.render(buffer, supersample)
        pygame.transform.smoothscale(buffer, (window.width, window.height),
                                     frame)
        screen.fill(window.background)
        screen.blit(frame, (0, 0))
        hud.draw(screen, env.world, dt)
        pygame.display.flip()

        if env.world.game_over:
            env.reset()
            hero = env.world.controllables[0]
            ai_indices = [i for i, a in enumerate(env.agents) if a is not hero]
            ai_actions = [0] * len(ai_indices)

    pygame.quit()


if __name__ == "__main__":
    main()
