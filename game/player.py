import math
import os
from typing import Dict, Optional, Tuple

import numpy as np
import pygame

from .terrain import Terrain

Color = Tuple[int, int, int]

_GLOVE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "glove.png",
)
_glove_base: Optional[pygame.Surface] = None
_glove_cache: Dict[Tuple, pygame.Surface] = {}


def _load_glove() -> pygame.Surface:
    global _glove_base
    if _glove_base is None:
        surf = pygame.image.load(_GLOVE_PATH).convert_alpha()
        rect = surf.get_bounding_rect()
        _glove_base = surf.subsurface(rect).copy()
    return _glove_base


def _tinted_glove(color: Color) -> pygame.Surface:
    key = ("base", color)
    if key not in _glove_cache:
        surf = _load_glove().copy()
        arr = pygame.surfarray.pixels3d(surf)
        r = arr[:, :, 0].astype(np.int16)
        g = arr[:, :, 1].astype(np.int16)
        b = arr[:, :, 2].astype(np.int16)
        mask = (r > 110) & (g < 130) & (b < 130)
        arr[mask, 0] = color[0]
        arr[mask, 1] = color[1]
        arr[mask, 2] = color[2]
        del arr
        _glove_cache[key] = surf
    return _glove_cache[key]


def _glove_sprite(color: Color, target_h: int, flip: bool) -> pygame.Surface:
    key = (color, target_h, flip)
    if key not in _glove_cache:
        base = _tinted_glove(color)
        ratio = base.get_width() / base.get_height()
        size = (max(1, int(target_h * ratio)), max(1, target_h))
        sprite = pygame.transform.smoothscale(base, size)
        if flip:
            sprite = pygame.transform.flip(sprite, True, False)
        _glove_cache[key] = sprite
    return _glove_cache[key]


class Player:
    def __init__(self, color: Color, x: float, facing: int = 1,
                 scale: float = 2.0, speed: float = 220.0, name: str = ""):
        self.name = name
        self.color = color
        self.x = x
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.facing = facing
        self.scale = scale
        self.speed = speed
        self.gravity = 2200.0
        self.jump_speed = 760.0
        self.accel = 1800.0
        self.max_speed = 260.0
        self.decel = 12.0
        self.on_ground = True
        self.walk_phase = 0.0
        self.moving = False
        self.angle = 0.0
        self.punch_timer = 0.0
        self.punch_duration = 0.35
        self.punch_cooldown = 1.0
        self.cooldown_timer = 0.0
        self.punch_hit = False
        self.punch_force = 1250.0
        self.punch_lift = 360.0
        self.punch_range = 27.0 * scale
        self.stun = 0.0
        self.stun_duration = 0.5
        self.score = 0
        self.alive = True
        self.zone_time = 0.0
        self.item = None

    @property
    def radius(self) -> float:
        return 9 * self.scale

    def in_zone(self, flag_x: float, half_width: float,
                ground_y: float) -> bool:
        return (self.alive and abs(self.x - flag_x) <= half_width and
                self.y <= ground_y + 30 * self.scale)

    def kill(self) -> None:
        self.alive = False
        self.vx = 0.0
        self.vy = 0.0
        self.stun = 0.0
        self.on_ground = False
        self.item = None

    def knockback(self, direction: int, force: float, lift: float,
                  stun: float) -> None:
        if not self.alive:
            return
        self.vx = direction * force
        self.vy = -lift
        self.on_ground = False
        self.stun = max(self.stun, stun)
        self.punch_timer = 0.0

    def use_item(self, world) -> None:
        if self.item is None or not self.alive or not self.on_ground:
            return
        self.item.use(world, self)
        self.item = None

    def update(self, dt: float, terrain: Terrain, move_dir: int,
               width: int, jump: bool = False) -> None:
        if self.stun > 0:
            self.stun = max(0.0, self.stun - dt)
            self.vx -= self.vx * min(1.0, 3.0 * dt)
        else:
            if move_dir != 0:
                self.facing = move_dir
                self.vx += move_dir * self.accel * dt
            else:
                self.vx -= self.vx * min(1.0, self.decel * dt)
            self.vx = max(-self.max_speed, min(self.max_speed, self.vx))
            if jump and self.on_ground:
                self.vy = -self.jump_speed
                self.on_ground = False
        self.x += self.vx * dt

        margin = 20 * self.scale
        if self.x < margin:
            self.x = margin
            self.vx = 0.0
        elif self.x > width - margin:
            self.x = width - margin
            self.vx = 0.0

        self.vy += self.gravity * dt
        self.y += self.vy * dt

        ground = terrain.height_at(self.x)
        if self.y >= ground:
            self.y = ground
            self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

        self.moving = self.on_ground and self.stun <= 0 and abs(self.vx) > 8
        if self.moving:
            self.walk_phase += dt * (abs(self.vx) / 60.0 + 4.0)

        e = 6.0
        slope = (terrain.height_at(self.x + e) -
                 terrain.height_at(self.x - e)) / (2 * e)
        self.angle = math.atan(slope)
        if self.punch_timer > 0:
            self.punch_timer = max(0.0, self.punch_timer - dt)
        if self.cooldown_timer > 0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

    def resolve_collision(self, other: "Player") -> None:
        overlap = self.radius + other.radius
        dx = other.x - self.x
        if abs(dx) >= overlap or abs(self.y - other.y) >= overlap:
            return
        sign = 1.0 if dx >= 0 else -1.0
        push = (overlap - abs(dx)) / 2.0
        self.x -= sign * push
        other.x += sign * push
        if sign > 0:
            self.vx = min(self.vx, 0.0)
            other.vx = max(other.vx, 0.0)
        else:
            self.vx = max(self.vx, 0.0)
            other.vx = min(other.vx, 0.0)

    def punch(self) -> None:
        if self.cooldown_timer <= 0:
            self.punch_timer = self.punch_duration
            self.cooldown_timer = self.punch_cooldown
            self.punch_hit = False

    def get_punched(self, direction: int) -> None:
        self.knockback(direction, self.punch_force, self.punch_lift,
                       self.stun_duration)

    def punch_amount(self) -> float:
        if self.punch_timer <= 0:
            return 0.0
        elapsed = self.punch_duration - self.punch_timer
        return math.sin(math.pi * elapsed / self.punch_duration)

    def draw(self, surface: pygame.Surface, ss: float = 1.0) -> None:
        scale = self.scale

        def s(v):
            return v * scale * ss

        cx = self.x * ss
        gy = self.y * ss
        theta = self.angle
        cos_t, sin_t = math.cos(theta), math.sin(theta)

        def rot(p):
            dx, dy = p[0] - cx, p[1] - gy
            return (cx + dx * cos_t - dy * sin_t,
                    gy + dx * sin_t + dy * cos_t)

        def line(a, b):
            a = rot(a)
            b = rot(b)
            pygame.draw.line(surface, self.color,
                             (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), lw)

        lw = max(2, int(3 * scale * ss))
        radius = s(9)
        leg_len = s(20)
        hip_y = gy - leg_len

        punch = self.punch_amount()
        reach = s(14) + punch * s(13)
        glove_anchor = rot((cx + self.facing * reach, hip_y - radius + s(6)))
        shoulder = rot((cx + self.facing * s(1), hip_y - s(2)))
        pygame.draw.line(surface, self.color,
                         (int(shoulder[0]), int(shoulder[1])),
                         (int(glove_anchor[0]), int(glove_anchor[1])), lw)

        stance = s(5)
        for i, phase in enumerate((self.walk_phase, self.walk_phase + math.pi)):
            lift = max(0.0, math.sin(phase)) * s(6) if self.moving else 0.0
            offset = stance if i == 0 else -stance
            ankle = (cx + self.facing * offset, gy - lift)
            line((cx, hip_y), ankle)
            line(ankle, (ankle[0] + self.facing * s(8), ankle[1]))

        center = rot((cx, hip_y - radius))
        pygame.draw.circle(surface, (255, 255, 255),
                           (int(center[0]), int(center[1])), int(radius))
        pygame.draw.circle(surface, self.color,
                           (int(center[0]), int(center[1])), int(radius), lw)

        eye = rot((cx + self.facing * s(4), hip_y - radius))
        pygame.draw.circle(surface, self.color,
                           (int(eye[0]), int(eye[1])), max(1, int(s(1.8))))

        glove = _glove_sprite(self.color, int(s(12)), self.facing < 0)
        glove = pygame.transform.rotate(glove, -math.degrees(theta))
        surface.blit(glove, (int(glove_anchor[0] - glove.get_width() / 2),
                             int(glove_anchor[1] - glove.get_height() / 2)))

        if self.stun > 0:
            t = pygame.time.get_ticks() / 120.0
            star_r = max(1, int(s(3.5)))
            for k in range(3):
                ang = t + k * (2 * math.pi / 3)
                sx = center[0] + math.cos(ang) * s(14)
                sy = center[1] - s(15) + math.sin(ang) * s(5)
                pygame.draw.circle(surface, (250, 210, 40),
                                   (int(sx), int(sy)), star_r)
                pygame.draw.circle(surface, (120, 90, 10),
                                   (int(sx), int(sy)), star_r, 1)

        if self.item is not None and self.alive:
            self.item.draw_held(surface, ss, self)
