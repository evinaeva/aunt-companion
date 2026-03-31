#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-/srv/gosha}"
MODEL_PATH="${MODEL_PATH:-$PROJECT_ROOT/data/models/llm/Qwen3-4B-Q5_K_M.gguf}"
PORT="${PORT:-8012}"
CTX="${CTX:-4096}"
THREADS="${THREADS:-$(nproc)}"

mkdir -p "$PROJECT_ROOT/data/logs"

exec "$PROJECT_ROOT/vendor/llama.cpp/build/bin/llama-server" \
  -m "$MODEL_PATH" \
  -c "$CTX" \
  -ngl 0 \
  -t "$THREADS" \
  --host 127.0.0.1 \
  --port "$PORT" \
  --jinja \
  >> "$PROJECT_ROOT/data/logs/llama.log" 2>&1
