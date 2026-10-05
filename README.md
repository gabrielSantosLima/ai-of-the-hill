# AI of the Hill

`ai-of-the-hill` is a game environment inspired by "King of the Hill" for
training Artificial Intelligence agents with Reinforcement Learning, built with
[pygame](https://www.pygame.org/) and [TorchRL](https://pytorch.org/rl/).

## Game rules

- The player must reach the top of the hill and stay **alone** inside the flag
  area for up to **20 seconds**.
- Each second the player earns **1 point**, but **only while alone** inside the
  area.
- If any other player enters the flag area, scoring is interrupted.
- To solve this, the player can **punch** opponents with their glove, **pushing**
  them down the hill.

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

### Running the Project

After activating the environment, run project commands from the repository root. Example:

```bash
python game/main.py
```

### Deactivating the Environment

```bash
deactivate
```
