# AI of the Hill - Python Setup

This project uses a local Python virtual environment and installs dependencies from `requirements.txt`.

## Requirements

- Python 3.10 or newer recommended
- The `python` command available in your terminal PATH
- `pip`, usually included with Python

## Windows Setup - PowerShell

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

## Linux Setup - Bash

From the project root, run:

```bash
chmod +x setup_env.sh
./setup_env.sh
```

Activate the environment with:

```bash
source .venv/bin/activate
```

## macOS Setup - Bash

From the project root, run:

```bash
chmod +x setup_env.sh
./setup_env.sh
```

Activate the environment with:

```bash
source .venv/bin/activate
```

## Manual Setup

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

## Running the Project

After activating the environment, run project commands from the repository root. Example:

```bash
python src/main.py
```

## Deactivating the Environment

```bash
deactivate
```
