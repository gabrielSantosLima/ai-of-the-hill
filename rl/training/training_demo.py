import math
import os
import random
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

import pygame

from game.config import DEFAULT_SCENE
from game.interface import ACTION_NAMES, GameInterface
from rl.observations import OBSERVATION_LABELS
from rl.sandbox import SandboxState, TrainingSandbox

NETWORK_LAYERS = [10, 8, 8, 8]


def mock_activations(elapsed: float):
    activations = []
    for li, count in enumerate(NETWORK_LAYERS):
        row = []
        for ni in range(count):
            value = 0.5 + 0.5 * math.sin(
                elapsed * (1.5 + 0.4 * li) + ni * 0.7 + li * 1.3)
            row.append(value)
        activations.append(row)
    return activations


def main() -> None:
    pygame.init()
    env = GameInterface(DEFAULT_SCENE)
    sandbox = TrainingSandbox(
        games=[env],
        game_size=(DEFAULT_SCENE.window.width, DEFAULT_SCENE.window.height),
        supersample=DEFAULT_SCENE.supersample,
        network_layers=NETWORK_LAYERS,
        title="Treino: demo (mock)",
    )
    screen = pygame.display.set_mode((sandbox.width, sandbox.height), vsync=1)
    pygame.display.set_caption("AI of the Hill - Training Sandbox")
    clock = pygame.time.Clock()

    env.reset()
    actions = [random.randrange(env.action_space_size)
               for _ in range(env.num_agents)]
    decision_timer = 0.0
    elapsed = 0.0
    generation = 1
    generation_timer = 0.0
    history = []

    running = True
    while running:
        dt = min(clock.tick(DEFAULT_SCENE.window.fps) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        elapsed += dt
        generation_timer += dt
        if generation_timer >= 12.0:
            generation_timer = 0.0
            history.append((generation, max(
                (p.score for p in env.agents), default=0)))
            generation += 1

        decision_timer += dt
        if decision_timer >= 0.3:
            decision_timer = 0.0
            actions = [random.randrange(env.action_space_size)
                       for _ in range(env.num_agents)]

        env.step([env.action_from_index(a) for a in actions])

        ordered = sorted(env.agents, key=lambda p: (p.score, p.alive),
                         reverse=True)
        best = ordered[0]
        ranking = [{"name": p.name, "color": p.color, "score": p.score,
                    "alive": p.alive} for p in ordered[:8]]
        state = SandboxState(
            generation=generation,
            population=env.num_agents,
            alive=sum(1 for p in env.agents if p.alive),
            record=max((p.score for p in env.agents), default=0),
            title="Treino: demo (mock)",
            network=mock_activations(elapsed),
            best=best,
            ranking=ranking,
            input_labels=OBSERVATION_LABELS,
            output_labels=ACTION_NAMES,
            history=history,
        )
        sandbox.draw(screen, state, dt)
        pygame.display.flip()

        if env.world.game_over:
            env.reset()
            actions = [random.randrange(env.action_space_size)
                       for _ in range(env.num_agents)]

    pygame.quit()


if __name__ == "__main__":
    main()
