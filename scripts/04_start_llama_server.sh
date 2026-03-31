#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-/srv/gosha}"
MODEL_PATH="${MODEL_PATH:-$PROJECT_ROOT/data/models/llm/Qwen3-4B-Q5_K_M.gguf}"
PORT="${PORT:-8012}"
CTX="${CTX:-4096}"
THREADS="${THREADS:-$(nproc)}"

if [ ! -x "$PROJECT_ROOT/vendor/llama.cpp/build/bin/llama-server" ]; then
  echo "llama-server binary not found. Run scripts/01_bootstrap_ubuntu.sh first." >&2
  exit 1
fi

if [ ! -f "$MODEL_PATH" ]; then
  echo "LLM model file not found: $MODEL_PATH" >&2
  exit 1
fi

echo "Starting llama.cpp server"
echo "  project: $PROJECT_ROOT"
echo "  model:   $MODEL_PATH"
echo "  host:    127.0.0.1"
echo "  port:    $PORT"
echo "  ctx:     $CTX"
echo "  threads: $THREADS"

exec "$PROJECT_ROOT/vendor/llama.cpp/build/bin/llama-server" \
  -m "$MODEL_PATH" \
  -c "$CTX" \
  -ngl 0 \
  -t "$THREADS" \
  --host 127.0.0.1 \
  --port "$PORT" \
  --jinja
