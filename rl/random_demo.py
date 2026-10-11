import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from game.config import DEFAULT_SCENE
from game.hud import HUD
from game.interface import GameInterface


def main() -> None:
    scene = DEFAULT_SCENE
    window = scene.window
    pygame.init()
    screen = pygame.display.set_mode((window.width, window.height), vsync=1)
    pygame.display.set_caption("AI of the Hill - RL random demo")
    clock = pygame.time.Clock()

    env = GameInterface(scene)
    hud = HUD(scene)
    supersample = max(1, scene.supersample)
    buffer = pygame.Surface(
        (window.width * supersample, window.height * supersample))
    frame = pygame.Surface((window.width, window.height))

    env.reset()
    actions = [random.randrange(env.action_space_size)
               for _ in range(env.num_agents)]
    decision_timer = 0.0

    def sample_actions():
        return [random.randrange(env.action_space_size)
                for _ in range(env.num_agents)]

    running = True
    while running:
        dt = min(clock.tick(window.fps) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        decision_timer += dt
        if decision_timer >= 0.2:
            decision_timer = 0.0
            actions = sample_actions()

        _, _, done, info = env.step(
            [env.action_from_index(a) for a in actions])

        buffer.fill(window.background)
        env.render(buffer, supersample)
        pygame.transform.smoothscale(buffer, (window.width, window.height),
                                     frame)
        screen.fill(window.background)
        screen.blit(frame, (0, 0))
        hud.draw(screen, env.world, dt)
        pygame.display.flip()

        if done:
            env.reset()
            actions = sample_actions()

    env.close()


if __name__ == "__main__":
    main()
