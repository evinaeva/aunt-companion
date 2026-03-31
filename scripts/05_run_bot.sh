#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-/srv/gosha}"
cd "$PROJECT_ROOT"

if [ ! -d ".venv" ]; then
  echo "Python virtualenv not found at $PROJECT_ROOT/.venv" >&2
  echo "Run scripts/01_bootstrap_ubuntu.sh first." >&2
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "Environment file not found at $PROJECT_ROOT/.env" >&2
  echo "Run scripts/03_create_env.sh and fill required values." >&2
  exit 1
fi

source .venv/bin/activate
set -a
source .env
set +a

echo "Starting Gosha bot"
echo "  project: $PROJECT_ROOT"
echo "  python:  $(command -v python)"

export PYTHONUNBUFFERED=1
exec python -m app.main
