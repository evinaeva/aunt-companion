#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-/srv/gosha}"
cd "$PROJECT_ROOT"

source .venv/bin/activate
set -a
source .env
set +a

mkdir -p "$PROJECT_ROOT/data/logs"

exec python -m app.main >> "$PROJECT_ROOT/data/logs/bot.log" 2>&1
