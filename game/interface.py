import os
import random
from typing import Dict, List, Optional, Tuple

import pygame

from .config import DEFAULT_SCENE, SceneConfig
from .player import Player
from .world import AgentAction, World

DISCRETE_ACTIONS: List[AgentAction] = [
    AgentAction(),
    AgentAction(move=-1),
    AgentAction(move=1),
    AgentAction(jump=True),
    AgentAction(punch=True),
    AgentAction(use_item=True),
    AgentAction(move=-1, jump=True),
    AgentAction(move=1, jump=True),
]

ACTION_NAMES = ["noop", "left", "right", "jump", "punch", "use", "left_jump",
                "right_jump"]


class GameInterface:
    BASE_OBSERVATION = 16
    PER_OTHER = 6
    PICKUP_OBSERVATION = 3

    def __init__(self, scene: Optional[SceneConfig] = None,
                 dt: Optional[float] = None):
        self.scene = scene or DEFAULT_SCENE
        self.dt = dt if dt is not None else 1.0 / self.scene.window.fps
        self.reward_score = 1.0
        self.reward_death = -1.0
        self.reward_zone = 0.05
        self._ensure_display()
        self.world = World(self.scene)
        self.agents: List[Player] = list(self.world.players)
        self._reset_counters()

    @staticmethod
    def _ensure_display() -> None:
        pygame.init()
        if pygame.display.get_surface() is not None:
            return
        try:
            pygame.display.set_mode((1, 1))
        except pygame.error:
            pygame.display.quit()
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.init()
            pygame.display.set_mode((1, 1))

    @property
    def num_agents(self) -> int:
        return len(self.agents)

    @property
    def action_space_size(self) -> int:
        return len(DISCRETE_ACTIONS)

    @property
    def observation_size(self) -> int:
        return (self.BASE_OBSERVATION +
                (self.num_agents - 1) * self.PER_OTHER +
                self.PICKUP_OBSERVATION)

    @staticmethod
    def action_from_index(index: int) -> AgentAction:
        return DISCRETE_ACTIONS[index]

    def _reset_counters(self) -> None:
        self._prev_scores = {id(p): p.score for p in self.agents}
        self._prev_alive = {id(p): p.alive for p in self.agents}

    def reset(self, seed: Optional[int] = None) -> List[List[float]]:
        if seed is not None:
            random.seed(seed)
        self.world = World(self.scene)
        self.agents = list(self.world.players)
        self._reset_counters()
        return self.observe()

    def set_action(self, agent: Player, action: AgentAction) -> None:
        self.world.set_action(agent, action)

    def _apply_actions(self, actions) -> None:
        if isinstance(actions, dict):
            for key, action in actions.items():
                agent = key if isinstance(key, Player) else self.agents[key]
                self.world.set_action(agent, action)
            return
        for agent, action in zip(self.agents, actions):
            self.world.set_action(agent, action)

    def step(self, actions=None
             ) -> Tuple[List[List[float]], List[float], bool, dict]:
        if actions is not None:
            self._apply_actions(actions)
        self.world.update(self.dt)
        rewards = self._compute_rewards()
        observation = self.observe()
        done = self.world.game_over
        info = self.get_state()
        return observation, rewards, done, info

    def _compute_rewards(self) -> List[float]:
        rewards: List[float] = []
        for player in self.agents:
            reward = (player.score - self._prev_scores[id(player)]
                      ) * self.reward_score
            if self._prev_alive[id(player)] and not player.alive:
                reward += self.reward_death
            if player.alive and player.in_zone(self.world.flag_x,
                                               self.world.zone_half,
                                               self.world.flag_ground_y):
                reward += self.reward_zone * self.dt
            rewards.append(reward)
        self._reset_counters()
        return rewards

    def observe(self) -> List[List[float]]:
        return [self.agent_observation(agent) for agent in self.agents]

    def agent_observation(self, agent: Player) -> List[float]:
        world = self.world
        width = self.world.level.width
        height = self.world.level.height
        max_speed = agent.max_speed if agent.max_speed else 1.0
        stun_max = agent.stun_duration if agent.stun_duration else 1.0
        obs = [
            agent.x / width,
            agent.y / height,
            max(-1.0, min(1.0, agent.vx / max_speed)),
            max(-1.0, min(1.0, agent.vy / 1000.0)),
            1.0 if agent.on_ground else 0.0,
            float(agent.facing),
            max(0.0, min(1.0, agent.stun / stun_max)),
            agent.score / self.scene.win_score,
            1.0 if agent.item is not None else 0.0,
            1.0 if agent.alive else 0.0,
            (world.flag_x - agent.x) / width,
            (world.flag_ground_y - agent.y) / height,
            1.0 if agent.in_zone(world.flag_x, world.zone_half,
                                 world.flag_ground_y) else 0.0,
            1.0 if world.lava.active else 0.0,
            (world.lava.surface_y - agent.y) / height,
            max(0.0, 1.0 - world.time / 180.0),
        ]
        for other in self.agents:
            if other is agent:
                continue
            obs.extend([
                (other.x - agent.x) / width,
                (other.y - agent.y) / height,
                max(-1.0, min(1.0, other.vx / max_speed)),
                1.0 if other.alive else 0.0,
                1.0 if other.item is not None else 0.0,
                1.0 if other.in_zone(world.flag_x, world.zone_half,
                                     world.flag_ground_y) else 0.0,
            ])
        if world.pickups:
            pickup = min(world.pickups,
                         key=lambda p: (p.x - agent.x) ** 2 +
                         (p.y - agent.y) ** 2)
            obs.extend([(pickup.x - agent.x) / width,
                        (pickup.y - agent.y) / height, 1.0])
        else:
            obs.extend([0.0, 0.0, 0.0])
        return obs

    def get_state(self) -> dict:
        world = self.world
        return {
            "time": world.time,
            "lava_active": world.lava.active,
            "lava_surface": world.lava.surface_y,
            "game_over": world.game_over,
            "winner": world.winner.name if world.winner else None,
            "agents": [
                {
                    "name": p.name,
                    "color": p.color,
                    "x": p.x,
                    "y": p.y,
                    "score": p.score,
                    "alive": p.alive,
                    "has_item": p.item is not None,
                    "in_zone": p.in_zone(world.flag_x, world.zone_half,
                                         world.flag_ground_y),
                    "stun": p.stun,
                }
                for p in self.agents
            ],
        }

    def render(self, surface: pygame.Surface, ss: float = 1.0) -> None:
        self.world.draw(surface, ss)

    def close(self) -> None:
        pygame.quit()
