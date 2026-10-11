from dataclasses import dataclass, field
from typing import List, Optional, Tuple

Point = Tuple[float, float]
Color = Tuple[int, int, int]


@dataclass
class LevelConfig:
    name: str
    width: int
    height: int
    control_points: List[Point]
    flag_height: float = 70.0
    flag_width: float = 40.0
    flag_x: Optional[float] = None

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

DEFAULT_SCENE = SceneConfig(
    level=SIMPLE_HILL,
    agents=[
        AgentConfig("blue", (70, 150, 255), 320, 1, controllable=True),
        AgentConfig("green", (60, 180, 90), 620, 1),
        AgentConfig("yellow", (225, 160, 20), 950, -1),
    ],
)
