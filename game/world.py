import math
import os
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pygame

from .background import Background
from .config import SceneConfig
from .elements import Flag
from .lava import Lava
from .pickups import Pickup
from .player import Player
from .powers import POWER_UPS, Explosion
from .sensors import DIRECTIONS, head_position, sensor_distances
from .terrain import Terrain

_LAVA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "lava_strip.png",
)

_FONTS: Dict[int, pygame.font.Font] = {}


def _font(size: int) -> pygame.font.Font:
    font = _FONTS.get(size)
    if font is None:
        font = pygame.font.Font(None, size)
        _FONTS[size] = font
    return font


@dataclass
class AgentAction:
    move: int = 0
    jump: bool = False
    punch: bool = False
    use_item: bool = False


class World:
    def __init__(self, scene: SceneConfig):
        self.scene = scene
        self.level = scene.level
        self.terrain = Terrain(scene.level)
        self.elements = [Flag(scene.level.flag_height, scene.level.flag_width)]
        self.players: List[Player] = []
        self.controllables: List[Player] = []
        self.actions: Dict[int, AgentAction] = {}
        self.external: set = set()
        self._ai_state: Dict[int, dict] = {}

        for agent in scene.agents:
            player = Player(agent.color, agent.x, agent.facing,
                            scene.character_scale, name=agent.name)
            self.players.append(player)
            if agent.controllable:
                self.controllables.append(player)
                self.external.add(id(player))
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
        self.zone_height = self.level.flag_zone_height
        self.lava = Lava(_LAVA_PATH, self.level, scene.window.height,
                         scene.lava_height_fraction)
        self.background = Background()
        self.shake_timer = 0.0
        self._shake: Tuple[float, float] = (0.0, 0.0)
        self.floaters: List[dict] = []
        self._backdrop_cache: Dict[Tuple[int, int, int], pygame.Surface] = {}
        self.pickups: List[Pickup] = []
        self.dynamites: List = []
        self.effects: List[Explosion] = []
        self._pickup_timer = random.uniform(6.0, 10.0)
        self._pickup_interval = (18.0, 30.0)
        self._pickup_margin = 90.0
        self._flag_pickup_weight = 0.25
        self.show_sensors = False

    def handle_keyboard(self) -> None:
        keys = pygame.key.get_pressed()
        for player in self.controllables:
            self.actions[id(player)] = AgentAction(
                move=int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) -
                int(keys[pygame.K_LEFT] or keys[pygame.K_a]),
                jump=bool(keys[pygame.K_UP] or keys[pygame.K_w]),
                punch=bool(keys[pygame.K_SPACE] or keys[pygame.K_j] or
                          keys[pygame.K_f]),
                use_item=bool(keys[pygame.K_e]),
            )

    def set_action(self, player: Player, action: AgentAction) -> None:
        self.actions[id(player)] = action

    def _ai_decide(self, player: Player, dt: float) -> AgentAction:
        state = self._ai_state[id(player)]
        state["timer"] += dt
        punch = state["timer"] >= state["punch_every"]
        if punch:
            state["timer"] = 0.0
        state["jump_timer"] += dt
        jump = state["jump_timer"] >= state["jump_every"]
        if jump:
            state["jump_timer"] = 0.0
        use = (player.item is not None and player.on_ground and
               random.random() < dt * 0.4)
        return AgentAction(move=state["dir"], jump=jump, punch=punch,
                           use_item=use)

    def _ai_turn(self, player: Player, move_dir: int) -> None:
        state = self._ai_state[id(player)]
        margin = 20 * player.scale
        if player.x <= margin + 0.5 and move_dir < 0:
            state["dir"] = 1
        elif player.x >= self.level.width - margin - 0.5 and move_dir > 0:
            state["dir"] = -1

    def update(self, dt: float) -> None:
        if self.game_over:
            return
        self.time += dt

        for player in self.players:
            if not player.alive:
                continue
            action = self.actions.get(id(player))
            if action is None and id(player) not in self.external:
                action = self._ai_decide(player, dt)
                self._ai_turn(player, action.move)
            if action is None:
                action = AgentAction()
            player.update(dt, self.terrain, action.move, self.level.width,
                          action.jump)
            if action.punch:
                player.punch()
            if action.use_item:
                player.use_item(self)

        self._resolve_punches()

        alive = [p for p in self.players if p.alive]
        for i in range(len(alive)):
            for j in range(i + 1, len(alive)):
                alive[i].resolve_collision(alive[j])

        self._update_pickups(dt)
        self._update_dynamites(dt)
        self._update_effects(dt)
        self._update_scoring(dt)
        self._update_lava(dt)
        self._update_winner()
        self._update_shake(dt)
        self._update_floaters(dt)

    def _sample_pickup_x(self) -> float:
        low = self._pickup_margin
        high = self.level.width - self._pickup_margin
        max_dist = max(self.flag_x - low, high - self.flag_x, 1.0)
        while True:
            x = random.uniform(low, high)
            dist = abs(x - self.flag_x) / max_dist
            weight = self._flag_pickup_weight + (1 - self._flag_pickup_weight) * dist
            if random.random() < weight:
                return x

    def _update_pickups(self, dt: float) -> None:
        self._pickup_timer -= dt
        if self._pickup_timer <= 0:
            self._pickup_timer = random.uniform(*self._pickup_interval)
            power = random.choice(list(POWER_UPS.values()))
            self.pickups.append(Pickup(power, self._sample_pickup_x()))
        for pickup in self.pickups:
            pickup.update(dt, self.terrain)
        for pickup in list(self.pickups):
            for player in self.players:
                if player.alive and player.item is None and pickup.overlaps(player):
                    pickup.power.on_pickup(self, player)
                    self.pickups.remove(pickup)
                    break

    def _update_dynamites(self, dt: float) -> None:
        for bomb in self.dynamites:
            bomb.update(dt)
        for bomb in [b for b in self.dynamites if b.exploded]:
            effect = Explosion(bomb.x, bomb.y - 10,
                               bomb.power.blast_radius, bomb.power)
            self.effects.append(effect)
            self._apply_blast(bomb.x, bomb.y, bomb.power, effect)
            self.dynamites.remove(bomb)

    def _apply_blast(self, x: float, y: float, power, effect=None) -> None:
        for player in self.players:
            if not player.alive:
                continue
            dx = player.x - x
            dy = player.y - y
            dist = math.hypot(dx, dy)
            if dist > power.blast_radius:
                continue
            if effect is not None:
                effect.hit.add(id(player))
            if dx == 0:
                direction = random.choice((-1, 1))
            else:
                direction = 1 if dx > 0 else -1
            falloff = 1.0 - 0.5 * (dist / power.blast_radius)
            player.knockback(direction, power.blast_force * falloff,
                             power.blast_lift * falloff, power.blast_stun)

    def _update_effects(self, dt: float) -> None:
        for effect in self.effects:
            effect.update(dt)
            if effect.power is None:
                continue
            radius = effect.current_radius()
            for player in self.players:
                if not player.alive or id(player) in effect.hit:
                    continue
                dist = math.hypot(player.x - effect.x, player.y - effect.y)
                if dist <= radius:
                    effect.hit.add(id(player))
                    direction = 1 if player.x >= effect.x else -1
                    falloff = 1.0 - 0.5 * min(1.0, dist / effect.radius)
                    player.knockback(direction,
                                     effect.power.blast_force * falloff,
                                     effect.power.blast_lift * falloff,
                                     effect.power.blast_stun)
        self.effects = [e for e in self.effects if not e.done]

    def _update_floaters(self, dt: float) -> None:
        for floater in self.floaters:
            floater["age"] += dt
        self.floaters = [f for f in self.floaters if f["age"] < f["life"]]

    def _update_scoring(self, dt: float) -> None:
        alive = [p for p in self.players if p.alive]
        in_zone = [p for p in alive
                   if p.in_zone(self.flag_x, self.zone_half,
                                self.flag_ground_y, self.zone_height)]
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
                    player.kill("lava")

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
        for pickup in self.pickups:
            pickup.draw(surface, ss)
        for player in self.players:
            if player.alive:
                player.draw(surface, ss)
        if self.show_sensors:
            self._draw_sensors(surface, ss)
        for bomb in self.dynamites:
            bomb.draw(surface, ss)
        for effect in self.effects:
            effect.draw(surface, ss)
        self._draw_floaters(surface, ss)

    def _draw_sensors(self, surface: pygame.Surface, ss: float) -> None:
        width = self.level.width
        colors = [(255, 90, 90), (90, 180, 255), (255, 190, 70),
                  (150, 255, 150), (255, 120, 200), (210, 255, 120)]
        directions = list(DIRECTIONS.values())
        for player in self.players:
            if not player.alive:
                continue
            hx, hy = head_position(player)
            distances = sensor_distances(self, player)
            for (dx, dy), distance, color in zip(directions, distances,
                                                 colors):
                length = min(distance if distance != math.inf else width,
                             width)
                end = (hx + dx * length, hy + dy * length)
                pygame.draw.line(surface, color, (int(hx * ss), int(hy * ss)),
                                 (int(end[0] * ss), int(end[1] * ss)), 2)
                pygame.draw.circle(surface, color,
                                   (int(end[0] * ss), int(end[1] * ss)), 3)
            pygame.draw.circle(surface, (255, 255, 255),
                               (int(hx * ss), int(hy * ss)), 3)

    def _draw_floaters(self, surface: pygame.Surface, ss: float) -> None:
        font = _font(int(58 * ss))
        outline = font.render("+1", True, (40, 25, 0))
        text = font.render("+1", True, (255, 215, 30))
        for floater in self.floaters:
            alpha = int(255 * max(0.0, 1.0 - floater["age"] / floater["life"]))
            outline.set_alpha(alpha)
            text.set_alpha(alpha)
            x = floater["x"] * ss - text.get_width() / 2
            y = (floater["y"] - floater["age"] * 60) * ss
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                surface.blit(outline, (int(x + ox), int(y + oy)))
            surface.blit(text, (int(x), int(y)))
