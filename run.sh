#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

pkill -f '[g]ame/main.py' 2>/dev/null || true
sleep 1

nohup ./.venv/bin/python game/main.py > /tmp/aoth.log 2>&1 &
sleep 1

pid=$(pgrep -f '[g]ame/main.py' | head -1)
echo "AI of the Hill started (pid $pid)"
echo "log: /tmp/aoth.log"
