from typing import Tuple

import pygame

from .config import LevelConfig
from .terrain import Terrain

Color = Tuple[int, int, int]


class Element:
    def draw(self, surface: pygame.Surface, level: LevelConfig,
             terrain: Terrain, ss: float = 1.0) -> None:
        raise NotImplementedError


class Flag(Element):
    def __init__(self, height: float = 70.0, width: float = 40.0,
                 color: Color = (220, 40, 40)):
        self.height = height
        self.width = width
        self.color = color

    def draw(self, surface, level, terrain, ss=1.0):
        x = level.flag_position()
        y = terrain.height_at(x)
        top = y - self.height
        pygame.draw.line(surface, (15, 15, 15), (x * ss, y * ss),
                         (x * ss, top * ss), max(1, int(3 * ss)))
        tri_h = self.width * 0.7
        points = [((x + 2) * ss, top * ss), ((x + 2) * ss, (top + tri_h) * ss),
                  ((x + self.width) * ss, (top + tri_h / 2) * ss)]
        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.aalines(surface, self.color, True, points)
