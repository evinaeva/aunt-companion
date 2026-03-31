#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-/srv/gosha}"

mkdir -p \
  "$PROJECT_ROOT/docs" \
  "$PROJECT_ROOT/contract/schemas" \
  "$PROJECT_ROOT/codex" \
  "$PROJECT_ROOT/prompts" \
  "$PROJECT_ROOT/app" \
  "$PROJECT_ROOT/data/db" \
  "$PROJECT_ROOT/data/models/llm" \
  "$PROJECT_ROOT/data/models/tts" \
  "$PROJECT_ROOT/data/cache/huggingface" \
  "$PROJECT_ROOT/data/cache/stt" \
  "$PROJECT_ROOT/data/cache/tts" \
  "$PROJECT_ROOT/data/tmp" \
  "$PROJECT_ROOT/data/logs" \
  "$PROJECT_ROOT/data/backups" \
  "$PROJECT_ROOT/deploy/systemd" \
  "$PROJECT_ROOT/scripts" \
  "$PROJECT_ROOT/tests"

touch \
  "$PROJECT_ROOT/app/__init__.py" \
  "$PROJECT_ROOT/app/main.py" \
  "$PROJECT_ROOT/app/config.py" \
  "$PROJECT_ROOT/app/bot.py" \
  "$PROJECT_ROOT/app/handlers.py" \
  "$PROJECT_ROOT/app/db.py" \
  "$PROJECT_ROOT/app/llm.py" \
  "$PROJECT_ROOT/app/stt.py" \
  "$PROJECT_ROOT/app/tts.py" \
  "$PROJECT_ROOT/app/memory.py" \
  "$PROJECT_ROOT/app/models.py" \
  "$PROJECT_ROOT/tests/test_user_isolation.py" \
  "$PROJECT_ROOT/tests/test_memory.py" \
  "$PROJECT_ROOT/tests/test_voice_pipeline.py"

echo "Created project tree at $PROJECT_ROOT"
