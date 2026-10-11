import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from game.config import DEFAULT_SCENE
from game.world import World


def main() -> None:
    scene = DEFAULT_SCENE
    window = scene.window
    pygame.init()
    screen = pygame.display.set_mode((window.width, window.height), vsync=1)
    pygame.display.set_caption("AI of the Hill")
    clock = pygame.time.Clock()

    supersample = max(1, scene.supersample)
    buffer = (
        pygame.Surface((window.width * supersample, window.height * supersample))
        if supersample > 1 else screen
    )

    world = World(scene)

    running = True
    while running:
        dt = clock.tick(window.fps) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        world.update(dt)
        buffer.fill(window.background)
        world.draw(buffer, supersample)
        if supersample > 1:
            pygame.transform.smoothscale(
                buffer, (window.width, window.height), screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
