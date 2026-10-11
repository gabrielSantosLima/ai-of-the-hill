import math
from typing import Dict

import pygame

Color = tuple

_FONTS: Dict[int, pygame.font.Font] = {}


def _font(size: int) -> pygame.font.Font:
    if size not in _FONTS:
        _FONTS[size] = pygame.font.Font(None, size)
    return _FONTS[size]


class PowerUp:
    name = "power"
    color = (255, 255, 255)

    def on_pickup(self, world, player) -> None:
        player.item = self

    def use(self, world, player) -> None:
        raise NotImplementedError

    def draw_held(self, surface: pygame.Surface, ss: float, player) -> None:
        raise NotImplementedError

    def draw_crate_emblem(self, surface: pygame.Surface, ss: float,
                          cx: float, cy: float, size: float) -> None:
        pygame.draw.circle(surface, self.color, (int(cx), int(cy)),
                           max(2, int(size)))


class DynamiteBomb:
    def __init__(self, x: float, y: float, power: "DynamitePower"):
        self.x = x
        self.y = y
        self.power = power
        self.fuse = power.fuse
        self.exploded = False

    def update(self, dt: float) -> None:
        self.fuse -= dt
        if self.fuse <= 0:
            self.fuse = 0.0
            self.exploded = True

    def draw(self, surface: pygame.Surface, ss: float) -> None:
        scale = 2.0
        s = scale * ss
        cx = self.x * ss
        gy = self.y * ss

        body = pygame.Rect(0, 0, int(self.power.stick_w * s),
                           int(self.power.stick_h * s))
        body.midbottom = (int(cx), int(gy))
        pygame.draw.rect(surface, self.power.color, body)
        pygame.draw.rect(surface, (40, 20, 20), body, max(1, int(2 * ss)))
        pygame.draw.line(surface, (60, 40, 20),
                         (body.centerx, body.top),
                         (body.centerx, body.top - int(6 * s)),
                         max(1, int(2 * ss)))

        ms = int(self.fuse * 1000)
        text = _font(int(24 * ss)).render(str(ms), True, (220, 20, 20))
        surface.blit(text, (int(cx - text.get_width() / 2),
                            int(body.top - int(8 * s) - text.get_height())))


class Explosion:
    def __init__(self, x: float, y: float, radius: float, power=None):
        self.x = x
        self.y = y
        self.radius = radius
        self.power = power
        self.t = 0.0
        self.life = 0.55
        self.hit = set()

    @property
    def done(self) -> bool:
        return self.t >= self.life

    def current_radius(self) -> float:
        return self.radius * min(1.0, self.t / self.life)

    def update(self, dt: float) -> None:
        self.t += dt

    def draw(self, surface: pygame.Surface, ss: float) -> None:
        ratio = min(1.0, self.t / self.life)
        r = int(self.radius * ratio * ss)
        if r <= 0:
            return
        cx, cy = int(self.x * ss), int(self.y * ss)
        pygame.draw.circle(surface, (255, 150, 40), (cx, cy), r)
        pygame.draw.circle(surface, (255, 225, 120), (cx, cy),
                           max(1, int(r * 0.8)), max(2, int(4 * ss)))


class DynamitePower(PowerUp):
    name = "dynamite"
    color = (215, 45, 45)
    fuse = 2.0
    blast_radius = 190.0
    blast_force = 1500.0
    blast_lift = 430.0
    blast_stun = 1.0
    stick_w = 4.0
    stick_h = 9.0

    def use(self, world, player) -> None:
        world.dynamites.append(DynamiteBomb(player.x, player.y, self))

    def draw_held(self, surface: pygame.Surface, ss: float, player) -> None:
        s = player.scale * ss
        cx = player.x * ss
        cy = (player.y - 52 * player.scale) * ss
        body = pygame.Rect(0, 0, int(self.stick_w * s), int(self.stick_h * s))
        body.midbottom = (int(cx), int(cy + 5 * s))
        pygame.draw.rect(surface, self.color, body)
        pygame.draw.rect(surface, (40, 20, 20), body, max(1, int(1.5 * s)))
        pygame.draw.line(surface, (60, 40, 20), (body.centerx, body.top),
                         (body.centerx, body.top - int(4 * s)),
                         max(1, int(1.5 * s)))


POWER_UPS: Dict[str, PowerUp] = {
    DynamitePower.name: DynamitePower(),
}
