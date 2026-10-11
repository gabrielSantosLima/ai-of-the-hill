import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from game.config import DEFAULT_SCENE
from game.hud import HUD
from game.world import World


def main() -> None:
    scene = DEFAULT_SCENE
    window = scene.window
    pygame.init()
    screen = pygame.display.set_mode((window.width, window.height), vsync=1)
    pygame.display.set_caption("AI of the Hill")
    clock = pygame.time.Clock()

    supersample = max(1, scene.supersample)
    buffer = pygame.Surface(
        (window.width * supersample, window.height * supersample))
    frame = pygame.Surface((window.width, window.height))

    world = World(scene)
    hud = HUD(scene)

    debug = bool(os.environ.get("AOTH_DEBUG"))
    frames = 0
    measured = 0.0

    running = True
    while running:
        dt = min(clock.tick(window.fps) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        world.update(dt)
        buffer.fill(window.background)
        world.draw(buffer, supersample)
        pygame.transform.smoothscale(buffer, (window.width, window.height),
                                     frame)
        offset = world.shake_offset()
        screen.fill(window.background)
        screen.blit(frame, (int(offset[0]), int(offset[1])))
        hud.draw(screen, world, dt)
        pygame.display.flip()

        if debug:
            frames += 1
            measured += dt
            if measured >= 1.0:
                print(f"fps={frames / measured:.1f}", flush=True)
                frames = 0
                measured = 0.0

    pygame.quit()


if __name__ == "__main__":
    main()
