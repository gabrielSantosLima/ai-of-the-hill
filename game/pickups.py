import math

import pygame

from .powers import PowerUp

Color = tuple


class Pickup:
    half_size = 16.0
    fall_speed = 78.0
    sway = 26.0

    def __init__(self, power: PowerUp, x: float, y: float = -70.0):
        self.power = power
        self.x = x
        self.y = y
        self.phase = (x * 0.05) % (2 * math.pi)
        self.landed = False

    def update(self, dt: float, terrain) -> None:
        if self.landed:
            return
        self.phase += dt * 1.6
        self.x += math.sin(self.phase) * self.sway * dt
        self.y += self.fall_speed * dt
        ground = terrain.height_at(self.x)
        if self.y >= ground:
            self.y = ground
            self.landed = True

    def overlaps(self, player) -> bool:
        dx = abs(player.x - self.x)
        dy = abs(player.y - self.y)
        reach = self.half_size + player.radius
        return dx <= reach and dy <= reach + 20 * player.scale

    def draw(self, surface: pygame.Surface, ss: float) -> None:
        s = 2.0 * ss
        cx = self.x * ss
        cy = self.y * ss
        half = self.half_size * s

        if not self.landed:
            canopy_cy = cy - half * 3.2
            canopy_r = half * 1.7
            pygame.draw.circle(surface, (235, 235, 235),
                               (int(cx), int(canopy_cy)), int(canopy_r))
            pygame.draw.circle(surface, (60, 60, 60),
                               (int(cx), int(canopy_cy)), int(canopy_r),
                               max(1, int(2 * ss)))
            for side in (-1, 1):
                pygame.draw.line(
                    surface, (60, 60, 60),
                    (int(cx + side * canopy_r * 0.75), int(canopy_cy +
                                                          canopy_r * 0.5)),
                    (int(cx + side * half), int(cy - half)),
                    max(1, int(1.5 * ss)))

        box = pygame.Rect(0, 0, int(half * 2), int(half * 2))
        box.midbottom = (int(cx), int(cy))
        pygame.draw.rect(surface, (185, 130, 70), box)
        pygame.draw.rect(surface, (60, 40, 20), box, max(1, int(2.5 * ss)))
        pygame.draw.line(surface, (60, 40, 20), (box.left, box.top),
                         (box.right, box.bottom), max(1, int(2 * ss)))
        pygame.draw.line(surface, (60, 40, 20), (box.right, box.top),
                         (box.left, box.bottom), max(1, int(2 * ss)))
        self.power.draw_crate_emblem(surface, ss, cx, box.centery, half * 0.5)
