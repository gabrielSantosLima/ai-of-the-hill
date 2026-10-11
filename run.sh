#!/bin/bash
set -e

cd "$(dirname "$0")"

# Usage: run.sh [target]
#   (no arg)  -> game/main.py
#   game      -> game/main.py
#   manual    -> rl/manual_demo.py
#   random    -> rl/random_demo.py
#   <path>    -> any python script (e.g. rl/my_demo.py)
TARGET="${1:-game/main.py}"
case "$TARGET" in
    game | main) TARGET="game/main.py" ;;
    manual) TARGET="rl/manual_demo.py" ;;
    random) TARGET="rl/random_demo.py" ;;
esac

if [ ! -f "$TARGET" ]; then
    echo "script not found: $TARGET" >&2
    exit 1
fi

pkill -f '[g]ame/main.py' 2>/dev/null || true
pkill -f '[r]l/.*\.py' 2>/dev/null || true
sleep 1

name=$(basename "$TARGET" .py)
log="/tmp/aoth_${name}.log"
nohup ./.venv/bin/python "$TARGET" > "$log" 2>&1 &
pid=$!
sleep 1

echo "AI of the Hill -> $TARGET (pid $pid)"
echo "log: $log"
