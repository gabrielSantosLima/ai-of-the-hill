import colorsys
import os
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

Point = Tuple[float, float]
Color = Tuple[int, int, int]

_GOLDEN_RATIO_CONJUGATE = 0.618033988749895


def random_colors(count: int, seed: Optional[int] = None) -> List[Color]:
    rng = random.Random(seed)
    start = rng.random()
    colors: List[Color] = []
    for i in range(count):
        hue = (start + i * _GOLDEN_RATIO_CONJUGATE) % 1.0
        saturation = 0.65 + 0.35 * (i % 2)
        value = 0.80 + 0.18 * ((i // 2) % 3) / 2
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        colors.append((int(r * 255), int(g * 255), int(b * 255)))
    return colors


@dataclass
class LevelConfig:
    name: str
    width: int
    height: int
    control_points: List[Point]
    flag_height: float = 70.0
    flag_width: float = 40.0
    flag_x: Optional[float] = None
    flag_zone_width: float = 130.0
    flag_zone_height: float = 300.0

    def peak(self) -> Point:
        return min(self.control_points, key=lambda p: p[1])

    def flag_position(self) -> float:
        if self.flag_x is not None:
            return self.flag_x
        return self.peak()[0]


@dataclass
class WindowConfig:
    width: int = 1280
    height: int = 640
    fps: int = 60
    background: Color = (255, 255, 255)


@dataclass
class AgentConfig:
    name: str
    color: Color
    x: float
    facing: int = 1
    controllable: bool = False


@dataclass
class SceneConfig:
    level: LevelConfig
    agents: List[AgentConfig] = field(default_factory=list)
    window: WindowConfig = field(default_factory=WindowConfig)
    character_scale: float = 2.0
    supersample: int = 2
    win_score: int = 30
    top_scores: int = 5
    max_zone_seconds: float = 20.0
    lava_start_time: float = 30.0
    lava_rise_duration: float = 12.0
    lava_height_fraction: float = 0.5
    shake_duration: float = 0.7
    shake_magnitude: float = 8.0


SIMPLE_HILL = LevelConfig(
    name="simple_hill",
    width=1280,
    height=640,
    control_points=[
        (0, 560), (170, 560), (330, 556),
        (440, 448), (510, 336), (565, 246),
        (615, 200), (700, 200), (785, 200),
        (835, 246), (890, 336), (960, 448),
        (1070, 556), (1170, 560), (1280, 560),
    ],
    flag_x=700,
)

def build_agents(count: int = 5, seed: Optional[int] = None,
                 level: Optional[LevelConfig] = None) -> List[AgentConfig]:
    level = level or SIMPLE_HILL
    colors = random_colors(count, seed)
    rng = random.Random(seed)
    flag_x = level.flag_position()
    zone = level.flag_zone_width / 2.0
    margin = 90.0

    def spawn_x() -> float:
        while True:
            x = rng.uniform(margin, level.width - margin)
            if abs(x - flag_x) > zone + 30.0:
                return x

    agents: List[AgentConfig] = []
    for i in range(count):
        agents.append(AgentConfig(f"player{i + 1}", colors[i], spawn_x(),
                                  rng.choice((-1, 1)),
                                  controllable=(i == 0)))
    return agents


_seed_env = os.environ.get("AOTH_SEED")
_default_seed = int(_seed_env) if _seed_env else None

DEFAULT_SCENE = SceneConfig(
    level=SIMPLE_HILL,
    agents=build_agents(5, _default_seed),
)
