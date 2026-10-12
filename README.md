# AI of the Hill

`ai-of-the-hill` is a game environment inspired by "King of the Hill" for
training Artificial Intelligence agents with Reinforcement Learning, built with
[pygame](https://www.pygame.org/) and [PyTorch](https://pytorch.org/)
(the training uses a custom population-based DQN).

## Game rules

- Reach the top of the hill and stay **alone** inside the flag area; each second
  alone earns **1 point** (maximum of **20 consecutive seconds**).
- If **two or more** players are inside the flag area, **nobody scores**.
- **Punch** opponents with your glove to push them down the hill.
- **Power-ups** drop from the sky in parachute crates. The current item is
  **dynamite**: plant it on the ground, wait for the **2-second fuse** (red
  millisecond counter), and it explodes, pushing everyone in range far away and
  knocking them out for 1 second.
- After **30 seconds**, a screen shake happens and **lava** rises from the bottom
  up to half the hill's height. Touching the lava is **death**.
- The winner is the first to reach **30 points** or the **last survivor**.

## Controls

| Action            | Keys                          |
| ----------------- | ----------------------------- |
| Move              | `←` `→` / `A` `D`             |
| Jump              | `↑` / `W`                     |
| Punch             | `Space` / `J` / `F`           |
| Use item          | `E`                           |
| Toggle sensor view| `T`                           |
| Restart (demos)   | `R`                           |
| Quit              | `Esc`                         |

## Running

Use the helper script from the repository root (it kills any previous instance,
starts the target in the background and prints the PID):

```bash
bash run.sh            # the game (game/main.py)
bash run.sh game       # same as above
bash run.sh manual     # you vs random agents (rl/manual_demo.py)
bash run.sh random     # random agents demo (rl/random_demo.py)
bash run.sh best       # you vs the trained AI (rl/manual_vs_best.py)
bash run.sh demo       # dashboard with mock values (rl/training/training_demo.py)
bash run.sh train      # DQN training with the dashboard (rl/training/training_koth_dqn.py)
bash run.sh rl/your_demo.py   # any script
```

## Project structure

- `game/` — the pygame game: sprites, terrain, scoring, physics, punch/push,
  power-ups, lava, sensors, and the RL bridge (`game/interface.py`).
- `rl/` — reinforcement learning code shared by all experiments:
  - `rl/dqn.py` — batched population DQN (one network per agent).
  - `rl/observations.py` — the observation vector built from the game.
  - `rl/sandbox.py` — the training dashboard (data-driven renderer).
  - `rl/manual_demo.py`, `rl/random_demo.py`, `rl/manual_vs_best.py` — demos.
  - `rl/training/` — training scripts (one file per training type).
- `assets/` — sprites and art used by the game (see credits below).
- `best_weights/` and `checkpoints/` — saved weights (not committed).

## Training (population DQN)

Each agent owns a small MLP (`10 -> 10 -> 10 -> 8`) and trains **locally** from
its own replay buffer. At the end of a generation, the best individual (by game
score) is **copied into the worst fraction** of the population with **weight
mutation** (evolutionary step). Everything is parameterized at the top of
`rl/training/training_koth_dqn.py`.

- **Observation (10):** time, Euclidean distance to the flag, six raycast
  proximity sensors from the head (left, right, and four diagonals, detecting
  terrain and other players), distance to the nearest power-up, and "has item".
- **Actions (8):** noop, left, right, jump, punch, use item, left+jump,
  right+jump.
- **Reward:** +1 per point; small penalty per second without scoring; penalty for
  missed punches; penalties for dying (larger for lava); shaping for approaching
  the flag and for standing in the zone.
- **Techniques:** Double DQN, target network, gradient clipping, reward scaling,
  LeakyReLU, epsilon-greedy exploration.

The training window is a **dashboard**: the game runs on the left (sensor view
with `T`), and on the right it shows the generation/individuals/alive counters, a
live ranking, the network activation of the best individual (hover nodes to see
their meaning and value), the best individual's zoomed view, and a
generation-vs-record chart.

## Assets and credits

All art assets are public domain / CC0:

- Glove and clock icons — FreeSVG.org (OpenClipart).
- Lava — OpenGameArt.org "16x16 and animated lava tile".
- Background — OpenGameArt.org "Pixel Art Mountains Parallax"
  (see `assets/bg/License.txt`).

## License

Distributed under the [MIT License](LICENSE). You are free to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the software, as
long as the copyright notice and permission notice are included. The software is
provided "as is", without warranty of any kind.

## Python Setup

This project uses a local Python virtual environment and installs dependencies from `requirements.txt`.

### Requirements

- Python 3.10 or newer recommended
- The `python` command available in your terminal PATH
- `pip`, usually included with Python

### Windows Setup - PowerShell

From the project root, run:

```powershell
.\setup_env.ps1
```

If PowerShell blocks script execution, allow scripts for the current terminal session and run the setup again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_env.ps1
```

Activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Linux Setup - Bash

From the project root, run:

```bash
chmod +x setup_env.sh
./setup_env.sh
```

Activate the environment with:

```bash
source .venv/bin/activate
```

### macOS Setup - Bash

From the project root, run:

```bash
chmod +x setup_env.sh
./setup_env.sh
```

Activate the environment with:

```bash
source .venv/bin/activate
```

### Manual Setup

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

#### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

### Deactivating the Environment

```bash
deactivate
```
