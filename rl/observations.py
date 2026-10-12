import math

import numpy as np

from game.sensors import sensor_distances

OBSERVATION_SIZE = 10

OBSERVATION_LABELS = [
    "tempo",
    "dist. bandeira",
    "sensor esq.",
    "sensor dir.",
    "sensor diag. cima esq.",
    "sensor diag. cima dir.",
    "sensor diag. baixo esq.",
    "sensor diag. baixo dir.",
    "dist. item",
    "tem item",
]


def build_observations(world, players, horizon: float = 30.0) -> np.ndarray:
    count = len(players)
    width = world.level.width
    height = world.level.height
    flag_x = world.flag_x
    flag_ground_y = world.flag_ground_y
    diagonal = math.hypot(width, height)

    xs = np.array([p.x for p in players], dtype=np.float32)
    ys = np.array([p.y for p in players], dtype=np.float32)
    alive = np.array([p.alive for p in players], dtype=bool)

    sensors = [np.ones(count, dtype=np.float32) for _ in range(6)]
    for i in range(count):
        if not alive[i]:
            continue
        distances = sensor_distances(world, players[i])
        for k, distance in enumerate(distances):
            if not math.isinf(distance):
                sensors[k][i] = min(1.0, distance / width)

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

    flag_distance = np.hypot(flag_x - xs, flag_ground_y - ys) / diagonal

    observation = np.empty((count, OBSERVATION_SIZE), dtype=np.float32)
    observation[:, 0] = min(1.0, world.time / horizon)
    observation[:, 1] = np.clip(flag_distance, 0.0, 1.0)
    for k in range(6):
        observation[:, 2 + k] = sensors[k]
    observation[:, 8] = power
    observation[:, 9] = np.array(
        [1.0 if p.item is not None else 0.0 for p in players],
        dtype=np.float32)
    return observation
