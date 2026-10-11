import os
import random
from typing import Dict, List, Optional, Tuple

import pygame

from .background import Background
from .config import SceneConfig
from .elements import Flag
from .lava import Lava
from .player import Player
from .terrain import Terrain

_LAVA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "lava_strip.png",
)

_FONT: Optional[pygame.font.Font] = None


def _font() -> pygame.font.Font:
    global _FONT
    if _FONT is None:
        _FONT = pygame.font.Font(None, 42)
    return _FONT


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
                            scene.character_scale, name=agent.name)
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

        self.time = 0.0
        self.game_over = False
        self.winner: Optional[Player] = None
        self.flag_x = self.level.flag_position()
        self.flag_ground_y = self.terrain.height_at(self.flag_x)
        self.zone_half = self.level.flag_zone_width / 2.0
        self.lava = Lava(_LAVA_PATH, self.level, scene.window.height,
                         scene.lava_height_fraction)
        self.background = Background()
        self.shake_timer = 0.0
        self._shake: Tuple[float, float] = (0.0, 0.0)
        self.floaters: List[dict] = []
        self._backdrop_cache: Dict[Tuple[int, int, int], pygame.Surface] = {}

    def update(self, dt: float) -> None:
        if self.game_over:
            return
        self.time += dt

        keys = pygame.key.get_pressed()
        for player in self.controllables:
            if not player.alive:
                continue
            move_dir = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - \
                int(keys[pygame.K_LEFT] or keys[pygame.K_a])
            jump = bool(keys[pygame.K_UP] or keys[pygame.K_w])
            player.update(dt, self.terrain, move_dir, self.level.width, jump)
            if keys[pygame.K_SPACE] or keys[pygame.K_j] or keys[pygame.K_f]:
                player.punch()

        for player in self.players:
            if not player.alive:
                continue
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

        alive = [p for p in self.players if p.alive]
        for i in range(len(alive)):
            for j in range(i + 1, len(alive)):
                alive[i].resolve_collision(alive[j])

        self._update_scoring(dt)
        self._update_lava(dt)
        self._update_winner()
        self._update_shake(dt)
        self._update_floaters(dt)

    def _update_floaters(self, dt: float) -> None:
        for floater in self.floaters:
            floater["age"] += dt
        self.floaters = [f for f in self.floaters if f["age"] < f["life"]]

    def _update_scoring(self, dt: float) -> None:
        alive = [p for p in self.players if p.alive]
        in_zone = [p for p in alive
                   if p.in_zone(self.flag_x, self.zone_half,
                                self.flag_ground_y)]
        if len(in_zone) == 1:
            player = in_zone[0]
            if player.zone_time < self.scene.max_zone_seconds:
                before = int(player.zone_time)
                player.zone_time = min(self.scene.max_zone_seconds,
                                       player.zone_time + dt)
                gained = int(player.zone_time) - before
                if gained > 0:
                    player.score += gained
                    self.floaters.append({
                        "x": player.x,
                        "y": player.y - 40 * player.scale,
                        "color": player.color,
                        "age": 0.0,
                        "life": 0.9,
                    })
            for other in alive:
                if other is not player:
                    other.zone_time = 0.0
        else:
            for player in alive:
                player.zone_time = 0.0

    def _update_lava(self, dt: float) -> None:
        if not self.lava.active and self.time >= self.scene.lava_start_time:
            self.lava.activate()
            self.shake_timer = self.scene.shake_duration
        self.lava.update(dt, self.scene.lava_rise_duration)
        if self.lava.active:
            for player in self.players:
                if player.alive and player.y >= self.lava.surface_y:
                    player.kill()

    def _update_winner(self) -> None:
        for player in self.players:
            if player.alive and player.score >= self.scene.win_score:
                self.winner = player
                self.game_over = True
                return
        alive = [p for p in self.players if p.alive]
        if len(alive) <= 1:
            self.winner = alive[0] if alive else None
            self.game_over = True

    def _update_shake(self, dt: float) -> None:
        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)
            ratio = self.shake_timer / self.scene.shake_duration
            mag = self.scene.shake_magnitude * ratio
            self._shake = (random.uniform(-mag, mag),
                           random.uniform(-mag, mag))
        else:
            self._shake = (0.0, 0.0)

    def shake_offset(self) -> Tuple[float, float]:
        return self._shake

    def _resolve_punches(self) -> None:
        for attacker in self.players:
            if not attacker.alive:
                continue
            if attacker.punch_timer <= 0 or attacker.punch_hit:
                continue
            if attacker.punch_amount() < 0.3:
                continue
            for target in self.players:
                if target is attacker or not target.alive:
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

    def _backdrop(self, surface: pygame.Surface,
                  ss: float) -> pygame.Surface:
        key = (int(ss), surface.get_width(), surface.get_height())
        backdrop = self._backdrop_cache.get(key)
        if backdrop is None:
            backdrop = pygame.Surface(surface.get_size())
            self.background.draw(backdrop, ss)
            self.terrain.draw(backdrop, ss)
            for element in self.elements:
                element.draw(backdrop, self.level, self.terrain, ss)
            self._backdrop_cache[key] = backdrop
        return backdrop

    def draw(self, surface: pygame.Surface, ss: float = 1.0) -> None:
        surface.blit(self._backdrop(surface, ss), (0, 0))
        self.lava.draw(surface, ss)
        for player in self.players:
            if player.alive:
                player.draw(surface, ss)
        self._draw_floaters(surface, ss)

    def _draw_floaters(self, surface: pygame.Surface, ss: float) -> None:
        font = _font()
        for floater in self.floaters:
            alpha = 1.0 - floater["age"] / floater["life"]
            text = font.render("+1", True, floater["color"])
            text.set_alpha(int(255 * max(0.0, alpha)))
            x = floater["x"] * ss - text.get_width() / 2
            y = (floater["y"] - floater["age"] * 60) * ss
            surface.blit(text, (int(x), int(y)))
