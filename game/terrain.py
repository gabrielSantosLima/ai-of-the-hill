from typing import List, Tuple

import pygame

from .config import LevelConfig

Point = Tuple[float, float]


def _catmull_rom(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    t2 = t * t
    t3 = t2 * t
    return (
        0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
               (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
               (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
        0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
               (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
               (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3),
    )


def smooth(points: List[Point], samples: int = 24) -> List[Point]:
    pts = [points[0]] + list(points) + [points[-1]]
    out: List[Point] = []
    for i in range(1, len(pts) - 2):
        for s in range(samples):
            out.append(_catmull_rom(pts[i - 1], pts[i], pts[i + 1], pts[i + 2],
                                    s / samples))
    out.append(points[-1])
    return out


class Terrain:
    def __init__(self, config: LevelConfig, samples: int = 24,
                 line_color=(15, 15, 15), line_width: int = 3):
        self.config = config
        self.samples = samples
        self.line_color = line_color
        self.line_width = line_width
        self._curve = smooth(config.control_points, samples)

    def curve(self) -> List[Point]:
        return self._curve

    def height_at(self, x: float) -> float:
        curve = self._curve
        if x <= curve[0][0]:
            return curve[0][1]
        for a, b in zip(curve, curve[1:]):
            if a[0] <= x <= b[0]:
                t = (x - a[0]) / (b[0] - a[0] + 1e-9)
                return a[1] + (b[1] - a[1]) * t
        return curve[-1][1]

    def draw(self, surface: pygame.Surface, ss: float = 1.0) -> None:
        cfg = self.config
        pts = [(int(x * ss), int(y * ss)) for x, y in self._curve]
        polygon = pts + [(int(cfg.width * ss), int(cfg.height * ss)), (0, int(cfg.height * ss))]
        pygame.draw.polygon(surface, (255, 255, 255), polygon)
        pygame.draw.lines(surface, self.line_color, False, pts,
                          max(1, int(self.line_width * ss)))
        pygame.draw.aalines(surface, self.line_color, False, pts)
