import math
from typing import Dict, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F

_PARAM_SHAPES = ("W1", "b1", "W2", "b2", "W3", "b3")


def get_device(preference: str = "auto") -> torch.device:
    if preference == "cpu":
        return torch.device("cpu")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


class DQNPopulation:
    def __init__(self, num_agents: int, observation_size: int, hidden: int,
                 num_actions: int, learning_rate: float, device: torch.device,
                 seed: Optional[int] = None):
        self.n = num_agents
        self.obs_dim = observation_size
        self.hidden = hidden
        self.actions = num_actions
        self.device = device
        if seed is not None:
            torch.manual_seed(seed)
        self.online = self._init_params(True)
        self.target = self._init_params(False)
        self.copy_to_target()
        self.optimizer = torch.optim.Adam(
            list(self.online.values()), lr=learning_rate)
        self.learn_steps = 0

    def _init_params(self, requires_grad: bool) -> Dict[str, torch.Tensor]:
        n, h, o, a = self.n, self.hidden, self.obs_dim, self.actions

        def weight(*shape):
            tensor = torch.empty(*shape, device=self.device)
            fan_in = shape[-1]
            bound = 1.0 / math.sqrt(fan_in)
            tensor.uniform_(-bound, bound)
            return torch.nn.Parameter(tensor, requires_grad=requires_grad)

        def bias(*shape):
            tensor = torch.zeros(*shape, device=self.device)
            return torch.nn.Parameter(tensor, requires_grad=requires_grad)

        return {
            "W1": weight(n, h, o), "b1": bias(n, h),
            "W2": weight(n, h, h), "b2": bias(n, h),
            "W3": weight(n, a, h), "b3": bias(n, a),
        }

    @staticmethod
    def _forward(theta: Dict[str, torch.Tensor],
                 x: torch.Tensor) -> torch.Tensor:
        h1 = F.leaky_relu(torch.einsum("nbi,nki->nbk", x, theta["W1"]) +
                          theta["b1"].unsqueeze(1), 0.01)
        h2 = F.leaky_relu(torch.einsum("nbi,nki->nbk", h1, theta["W2"]) +
                          theta["b2"].unsqueeze(1), 0.01)
        return torch.einsum("nbi,nki->nbk", h2, theta["W3"]) + \
            theta["b3"].unsqueeze(1)

    def layer_activations(self, observations: torch.Tensor
                          ) -> Tuple[np.ndarray, np.ndarray, np.ndarray,
                                     np.ndarray]:
        with torch.no_grad():
            x = observations.unsqueeze(1)
            h1 = F.leaky_relu(
                torch.einsum("nbi,nki->nbk", x, self.online["W1"]) +
                self.online["b1"].unsqueeze(1), 0.01)
            h2 = F.leaky_relu(
                torch.einsum("nbi,nki->nbk", h1, self.online["W2"]) +
                self.online["b2"].unsqueeze(1), 0.01)
            q = torch.einsum("nbi,nki->nbk", h2, self.online["W3"]) + \
                self.online["b3"].unsqueeze(1)
            return (
                observations.detach().cpu().numpy(),
                h1.squeeze(1).detach().cpu().numpy(),
                h2.squeeze(1).detach().cpu().numpy(),
                q.squeeze(1).detach().cpu().numpy(),
            )

    def copy_to_target(self) -> None:
        for name in _PARAM_SHAPES:
            self.target[name].data.copy_(self.online[name].data)

    def act(self, observations: torch.Tensor, epsilon: float) -> torch.Tensor:
        with torch.no_grad():
            q_values = self._forward(self.online, observations.unsqueeze(1))
            greedy = q_values.squeeze(1).argmax(dim=1)
            random_actions = torch.randint(0, self.actions, (self.n,),
                                           device=self.device)
            explore = torch.rand(self.n, device=self.device) < epsilon
            return torch.where(explore, random_actions, greedy)

    def train(self, obs: torch.Tensor, nxt: torch.Tensor, act: torch.Tensor,
              rew: torch.Tensor, done: torch.Tensor, gamma: float,
              target_update: int, grad_clip: float = 0.0) -> float:
        q_values = self._forward(self.online, obs)
        q_selected = q_values.gather(2, act.unsqueeze(2)).squeeze(2)
        with torch.no_grad():
            next_actions = self._forward(self.online, nxt).argmax(
                dim=2, keepdim=True)
            q_next = self._forward(self.target, nxt).gather(
                2, next_actions).squeeze(2)
            target = rew + gamma * q_next * (1.0 - done)
        loss = F.smooth_l1_loss(q_selected, target)
        self.optimizer.zero_grad()
        loss.backward()
        if grad_clip > 0:
            torch.nn.utils.clip_grad_norm_(list(self.online.values()),
                                           grad_clip)
        self.optimizer.step()
        self.learn_steps += 1
        if target_update > 0 and self.learn_steps % target_update == 0:
            self.copy_to_target()
        return float(loss.item())

    def evolve(self, scores: torch.Tensor, replace_fraction: float,
               mutation_prob: float, mutation_std: float) -> int:
        replace_count = max(1, int(self.n * replace_fraction))
        worst = torch.argsort(scores)[:replace_count]
        best = int(torch.argmax(scores).item())
        row_mask = torch.zeros(self.n, dtype=torch.bool, device=self.device)
        row_mask[worst] = True
        for name in _PARAM_SHAPES:
            param = self.online[name]
            view = [1] * param.dim()
            view[0] = self.n
            param.data[worst] = param.data[best].unsqueeze(0).expand(
                replace_count, *param.shape[1:])
            mutate = row_mask.view(view) & (
                torch.rand_like(param) < mutation_prob)
            param.data += mutate.float() * torch.randn_like(param) * mutation_std
        self._reset_optimizer_state(worst)
        self.copy_to_target()
        return best

    def _reset_optimizer_state(self, indices: torch.Tensor) -> None:
        for param in self.online.values():
            state = self.optimizer.state.get(param)
            if not state:
                continue
            for key in ("exp_avg", "exp_avg_sq"):
                if key in state:
                    state[key][indices] = 0.0

    def agent_weights(self, index: int) -> Dict[str, torch.Tensor]:
        return {name: self.online[name][index].detach().cpu().clone()
                for name in _PARAM_SHAPES}

    def state_dict(self) -> Dict[str, torch.Tensor]:
        return {name: self.online[name].detach().cpu().clone()
                for name in _PARAM_SHAPES}

    def load_state_dict(self, state: Dict[str, torch.Tensor]) -> None:
        for name in _PARAM_SHAPES:
            self.online[name].data.copy_(state[name].to(self.device))
        self.copy_to_target()


class SingleAgentDQN:
    def __init__(self, weights: Dict[str, torch.Tensor],
                 device: torch.device):
        self.device = device
        self.w = {name: weights[name].to(device).float()
                  for name in _PARAM_SHAPES}

    @classmethod
    def load(cls, path: str, device: torch.device) -> "SingleAgentDQN":
        checkpoint = torch.load(path, map_location=device)
        return cls(checkpoint["weights"], device)

    def q_values(self, observations: torch.Tensor) -> torch.Tensor:
        h1 = F.leaky_relu(observations @ self.w["W1"].t() + self.w["b1"], 0.01)
        h2 = F.leaky_relu(h1 @ self.w["W2"].t() + self.w["b2"], 0.01)
        return h2 @ self.w["W3"].t() + self.w["b3"]

    def act(self, observations: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            return self.q_values(observations).argmax(dim=1)


class ReplayBuffer:
    def __init__(self, num_agents: int, capacity: int, obs_dim: int,
                 device: torch.device):
        self.n = num_agents
        self.capacity = capacity
        self.device = device
        self.obs = torch.zeros(num_agents, capacity, obs_dim, device=device)
        self.next = torch.zeros(num_agents, capacity, obs_dim, device=device)
        self.act = torch.zeros(num_agents, capacity, dtype=torch.long,
                               device=device)
        self.rew = torch.zeros(num_agents, capacity, device=device)
        self.done = torch.zeros(num_agents, capacity, device=device)
        self.ptr = 0
        self.size = 0

    def push(self, obs, act, rew, nxt, done) -> None:
        index = self.ptr
        self.obs[:, index] = obs
        self.act[:, index] = act
        self.rew[:, index] = rew
        self.next[:, index] = nxt
        self.done[:, index] = done
        self.ptr = (self.ptr + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch: int):
        rows = torch.arange(self.n, device=self.device)[:, None]
        cols = torch.randint(0, self.size, (self.n, batch),
                             device=self.device)
        return (self.obs[rows, cols], self.next[rows, cols],
                self.act[rows, cols], self.rew[rows, cols],
                self.done[rows, cols])
