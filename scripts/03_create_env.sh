#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-/srv/gosha}"

if [ ! -f "$PROJECT_ROOT/.env" ]; then
  cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  echo "Created $PROJECT_ROOT/.env from .env.example"
else
  echo "$PROJECT_ROOT/.env already exists"
fi

echo "LLM config: create $PROJECT_ROOT/config/llm.local.toml manually from config/llm.example.toml when ready"
