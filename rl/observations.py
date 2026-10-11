import math

import numpy as np

OBSERVATION_SIZE = 7


def build_observations(world, players, horizon: float = 60.0) -> np.ndarray:
    count = len(players)
    width = world.level.width
    height = world.level.height
    flag_x = world.flag_x
    flag_ground_y = world.flag_ground_y

    xs = np.array([p.x for p in players], dtype=np.float32)
    ys = np.array([p.y for p in players], dtype=np.float32)
    alive = np.array([p.alive for p in players], dtype=bool)

    left = np.ones(count, dtype=np.float32)
    right = np.ones(count, dtype=np.float32)
    for i in range(count):
        if not alive[i]:
            continue
        for j in range(count):
            if j == i or not alive[j]:
                continue
            delta = xs[j] - xs[i]
            if delta < 0:
                dist = -delta / width
                if dist < left[i]:
                    left[i] = dist
            elif delta > 0:
                dist = delta / width
                if dist < right[i]:
                    right[i] = dist

    pickups = world.pickups
    power = np.ones(count, dtype=np.float32)
    for i in range(count):
        best = None
        for pickup in pickups:
            dist = math.hypot(pickup.x - xs[i], pickup.y - ys[i]) / width
            if best is None or dist < best:
                best = dist
        if best is not None:
            power[i] = min(1.0, best)

    time_norm = min(1.0, world.time / horizon)
    observation = np.empty((count, OBSERVATION_SIZE), dtype=np.float32)
    observation[:, 0] = time_norm
    observation[:, 1] = (flag_x - xs) / width
    observation[:, 2] = (flag_ground_y - ys) / height
    observation[:, 3] = left
    observation[:, 4] = right
    observation[:, 5] = power
    observation[:, 6] = np.array(
        [1.0 if p.item is not None else 0.0 for p in players],
        dtype=np.float32)
    return observation
