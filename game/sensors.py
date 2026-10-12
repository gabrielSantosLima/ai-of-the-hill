import math
from typing import Optional, Tuple

HEAD_OFFSET = 29.0
HEAD_TOP_OFFSET = 38.0
STEP = 4.0
_SQRT2 = math.sqrt(2.0)

DIRECTIONS = {
    "left": (-1.0, 0.0),
    "right": (1.0, 0.0),
    "up_left": (-_SQRT2 / 2.0, -_SQRT2 / 2.0),
    "up_right": (_SQRT2 / 2.0, -_SQRT2 / 2.0),
    "down_left": (-_SQRT2 / 2.0, _SQRT2 / 2.0),
    "down_right": (_SQRT2 / 2.0, _SQRT2 / 2.0),
}


def head_position(player) -> Tuple[float, float]:
    return (player.x, player.y - HEAD_OFFSET * player.scale)


def _terrain_hit(world, hx: float, hy: float, dx: float, dy: float,
                 max_range: float) -> Optional[float]:
    width = world.level.width
    height = world.level.height
    t = STEP
    while t <= max_range:
        x = hx + dx * t
        y = hy + dy * t
        if x < 0.0 or x > width or y < 0.0 or y > height:
            return None
        if y >= world.terrain.height_at(x):
            return t
        t += STEP
    return None


def _ray_box(ox: float, oy: float, dx: float, dy: float, left: float,
             top: float, right: float, bottom: float,
             max_range: float) -> Optional[float]:
    tmin, tmax = 0.0, max_range
    for origin, direction, low, high in ((ox, dx, left, right),
                                         (oy, dy, top, bottom)):
        if abs(direction) < 1e-9:
            if origin < low or origin > high:
                return None
        else:
            t1 = (low - origin) / direction
            t2 = (high - origin) / direction
            if t1 > t2:
                t1, t2 = t2, t1
            tmin = max(tmin, t1)
            tmax = min(tmax, t2)
            if tmin > tmax:
                return None
    return tmin


def _players_hit(world, player, hx: float, hy: float, dx: float, dy: float,
                 max_range: float) -> Optional[float]:
    best: Optional[float] = None
    for other in world.players:
        if other is player or not other.alive:
            continue
        radius = other.radius
        hit = _ray_box(hx, hy, dx, dy, other.x - radius,
                       other.y - HEAD_TOP_OFFSET * other.scale,
                       other.x + radius, other.y, max_range)
        if hit is not None and (best is None or hit < best):
            best = hit
    return best


def _cast(world, player, hx: float, hy: float, dx: float, dy: float,
          max_range: float) -> float:
    hits = [d for d in (_terrain_hit(world, hx, hy, dx, dy, max_range),
                        _players_hit(world, player, hx, hy, dx, dy,
                                     max_range))
            if d is not None]
    if not hits:
        return math.inf
    return min(hits)


def sensor_distances(world, player) -> Tuple[float, ...]:
    hx, hy = head_position(player)
    max_range = float(world.level.width)
    values = [_cast(world, player, hx, hy, dx, dy, max_range)
              for dx, dy in DIRECTIONS.values()]
    return tuple(values)
