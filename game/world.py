import random
from typing import Dict, List

import pygame

from .config import SceneConfig
from .elements import Flag
from .player import Player
from .terrain import Terrain


class World:
    def __init__(self, scene: SceneConfig):
        self.scene = scene
        self.level = scene.level
        self.terrain = Terrain(scene.level)
        self.elements = [Flag(scene.level.flag_height, scene.level.flag_width)]
        self.players: List[Player] = []
        self.controllables: List[Player] = []
        self._ai_state: Dict[int, dict] = {}

        for agent in scene.agents:
            player = Player(agent.color, agent.x, agent.facing,
                            scene.character_scale)
            self.players.append(player)
            if agent.controllable:
                self.controllables.append(player)
            else:
                self._ai_state[id(player)] = {
                    "dir": agent.facing,
                    "timer": random.uniform(0.5, 2.0),
                    "punch_every": random.uniform(1.5, 3.0),
                    "jump_timer": random.uniform(1.0, 3.0),
                    "jump_every": random.uniform(1.5, 4.0),
                }

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        for player in self.controllables:
            move_dir = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - \
                int(keys[pygame.K_LEFT] or keys[pygame.K_a])
            jump = bool(keys[pygame.K_SPACE] or keys[pygame.K_UP] or
                        keys[pygame.K_w])
            player.update(dt, self.terrain, move_dir, self.level.width, jump)
            if keys[pygame.K_j] or keys[pygame.K_f]:
                player.punch()

        for player in self.players:
            state = self._ai_state.get(id(player))
            if state is None:
                continue
            state["timer"] += dt
            if state["timer"] >= state["punch_every"]:
                state["timer"] = 0.0
                player.punch()
            state["jump_timer"] += dt
            jump = False
            if state["jump_timer"] >= state["jump_every"]:
                state["jump_timer"] = 0.0
                jump = True
            move_dir = state["dir"]
            player.update(dt, self.terrain, move_dir, self.level.width, jump)
            margin = 20 * player.scale
            if player.x <= margin + 0.5 and move_dir < 0:
                state["dir"] = 1
            elif player.x >= self.level.width - margin - 0.5 and move_dir > 0:
                state["dir"] = -1

        self._resolve_punches()

        for i in range(len(self.players)):
            for j in range(i + 1, len(self.players)):
                self.players[i].resolve_collision(self.players[j])

    def _resolve_punches(self) -> None:
        for attacker in self.players:
            if attacker.punch_timer <= 0 or attacker.punch_hit:
                continue
            if attacker.punch_amount() < 0.3:
                continue
            for target in self.players:
                if target is attacker:
                    continue
                dx = target.x - attacker.x
                dy = target.y - attacker.y
                if dx * attacker.facing <= 0:
                    continue
                if abs(dx) > attacker.punch_range + target.radius:
                    continue
                if abs(dy) > attacker.radius * 2.5:
                    continue
                target.get_punched(attacker.facing)
                attacker.punch_hit = True
                break

    def draw(self, surface: pygame.Surface, ss: float = 1.0) -> None:
        self.terrain.draw(surface, ss)
        for element in self.elements:
            element.draw(surface, self.level, self.terrain, ss)
        for player in self.players:
            player.draw(surface, ss)
