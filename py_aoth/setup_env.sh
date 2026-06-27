#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python is not installed or is not available in PATH."
    exit 1
fi

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "Error: requirements.txt was not found at: $REQUIREMENTS_FILE"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment at: $VENV_DIR"
    python3 -m venv "$VENV_DIR"
else
    echo "Python virtual environment already exists at: $VENV_DIR"
fi

if [ -x "$VENV_DIR/bin/python3" ]; then
    VENV_PYTHON="$VENV_DIR/bin/python3"
    ACTIVATE_COMMAND="source .venv/bin/activate"
elif [ -x "$VENV_DIR/Scripts/python.exe" ]; then
    VENV_PYTHON="$VENV_DIR/Scripts/python.exe"
    ACTIVATE_COMMAND="source .venv/Scripts/activate"
else
    echo "Error: virtual environment Python executable was not found."
    echo "Checked:"
    echo "  $VENV_DIR/bin/python3"
    echo "  $VENV_DIR/Scripts/python.exe"
    exit 1
fi

echo "Upgrading pip..."
"$VENV_PYTHON" -m pip install --upgrade pip

echo "Installing requirements from: $REQUIREMENTS_FILE"
"$VENV_PYTHON" -m pip install -r "$REQUIREMENTS_FILE"

echo ""
echo "Setup complete."
echo "To activate the environment, run:"
echo "  $ACTIVATE_COMMAND"
