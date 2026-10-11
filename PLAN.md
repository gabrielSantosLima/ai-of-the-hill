# Implementation Plan

Plan for building `ai-of-the-hill`, a "King of the Hill" environment for
training RL agents with pygame and TorchRL.

## Stage 1 — Build the game (`game/`)

- **1.a Player sprite:** `Player` class with per-agent color, hill physics, and
  glove/punch rendering.
- **1.b Generic level:** `map.py` builds the arena from configuration (hill
  height points, flag area, spawn coordinates); black and white aesthetic.
- **1.c Scoring:** `scoring.py` detects whether the player is alone in the flag
  area, tracks the 20-second counter, and awards 1 point per second.
- **1.d Mechanics:** `mechanics.py` handles punch collision and downhill
  knockback.
- **Loop:** `game.py` / `main.py` handles the game loop, camera, and
  orchestration.

## Stage 2 — Training module (`training/`)

- Parameterized TorchRL environment (number of agents, speed, damage, etc.).
- RL training loop, always saving the best individual to `best_weights/`.
- Dashboard with:
  - **2.a** The game running in the center.
  - **2.b** The neural network visually being activated.
  - **2.c** The best individual's view (with its score).
  - **2.d** Generation and number of individuals.
- Extract a headless, importable core from the game so training does not depend
  on the pygame display.

## Stage 3 — Play mode (`play/`)

- Load weights from `best_weights/`.
- One human-controlled character and one controlled by the best individual.
- Option to run only the AI (demo/observation mode).

## Open decisions

1. RL algorithm: PPO (TorchRL) or an evolutionary/NEAT approach as in the
   reference?
2. Number of simultaneous agents per episode (two or more)?
3. Observation representation: pixels (CNN) or state vector
   (positions/velocities)?
