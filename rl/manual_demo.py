import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from game.config import DEFAULT_SCENE
from game.hud import HUD
from game.interface import GameInterface
from game.world import AgentAction


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
    scene = DEFAULT_SCENE
    window = scene.window
    pygame.init()
    screen = pygame.display.set_mode((window.width, window.height), vsync=1)
    pygame.display.set_caption("AI of the Hill - Manual vs Random")
    clock = pygame.time.Clock()

    env = GameInterface(scene)
    hud = HUD(scene)
    supersample = max(1, scene.supersample)
    buffer = pygame.Surface(
        (window.width * supersample, window.height * supersample))
    frame = pygame.Surface((window.width, window.height))

    env.reset()
    hero = env.world.controllables[0]
    random_agents = [a for a in env.agents if a is not hero]
    random_actions = {a: random.randrange(env.action_space_size)
                      for a in random_agents}
    decision_timer = 0.0

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
                    random_agents = [a for a in env.agents if a is not hero]

        decision_timer += dt
        if decision_timer >= 0.2:
            decision_timer = 0.0
            random_actions = {a: random.randrange(env.action_space_size)
                              for a in random_agents}

        actions = {hero: player_action(pygame.key.get_pressed())}
        for agent in random_agents:
            actions[agent] = env.action_from_index(random_actions[agent])
        _, _, done, info = env.step(actions)

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
            hero = env.world.controllables[0]
            random_agents = [a for a in env.agents if a is not hero]

    env.close()


if __name__ == "__main__":
    main()
