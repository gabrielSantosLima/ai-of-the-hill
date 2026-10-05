# AGENTS.md

Guide for AI agents (and people) working on this repository.

## Overview

`ai-of-the-hill` is a game environment inspired by "King of the Hill" for
training RL agents. Main stack: **Python + pygame** (game and rendering) and
**TorchRL/PyTorch** (training). The game rules are described in the
[README](README.md#game-rules).

The project is still in its early stages. Review the scope by stage below
before implementing anything and keep it updated as work progresses.

## Environment

Always use the local virtualenv `.venv`.

- Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
- Linux/macOS (Bash): `source .venv/bin/activate`
- Setup: `.\setup_env.ps1` or `./setup_env.sh`
- Dependency installation: `python -m pip install -r requirements.txt`

## Useful commands

| Action                       | Command                                      |
| ---------------------------- | -------------------------------------------- |
| Run the game                 | `python game/main.py`                        |
| Install dependencies         | `python -m pip install -r requirements.txt`  |

> There is no test suite, linter, or type checker configured yet. When adding
> them, register the official command here (e.g., `pytest`, `ruff`, `mypy`) and
> prefer running them before finishing a task.

## Structure and conventions

- `game/` — pygame game: sprites, levels, scoring, and mechanics.
- `training/` — (planned) TorchRL training and dashboard.
- `play/` — (planned) human vs. best individual mode.
- `best_weights/` — (planned) best individual weights.

Conventions:

- **Aesthetic:** keep the black and white style for scenery/outlines; only the
  players get distinct colors.
- **Levels:** built generically and configurably, to allow new arenas without
  rewriting the game logic.
- **Scoring:** 1 point per second, only while the player is alone in the flag
  area (maximum of 20 consecutive seconds).
- **Determinism/parameterization:** the training module must be parameterized;
  always save the best individual to `best_weights/`.
- Do not add comments to the code unless requested.
- Write code and commit messages in **English**.

## Scope by stage

1. **Game:** player sprite, generic level, scoring, and punch/push mechanics.
2. **Training:** TorchRL environment + dashboard (game in the center, network
   activation, best individual view, and generation statistics).
3. **Play:** human vs. best individual, with an option to run only the AI.

## Best practices

- Do not commit weights, checkpoints, or `.venv` (see `.gitignore`).
- Do not introduce new dependencies without checking whether they already
  exist in `requirements.txt`.
- Before finishing a task, run the available verification commands and update
  the README/AGENTS if anything changes.
- Never commit/push without an explicit user request.
