#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-/srv/gosha}"
mkdir -p \
  "$PROJECT_ROOT/data/models/llm" \
  "$PROJECT_ROOT/data/models/tts" \
  "$PROJECT_ROOT/data/cache/huggingface"

export HF_HOME="$PROJECT_ROOT/data/cache/huggingface"

# Default lightweight LLM for CPU-friendly MVP
curl -L \
  "https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q5_K_M.gguf?download=true" \
  -o "$PROJECT_ROOT/data/models/llm/Qwen3-4B-Q5_K_M.gguf"

# Optional higher-quality 8-bit model
curl -L \
  "https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q8_0.gguf?download=true" \
  -o "$PROJECT_ROOT/data/models/llm/Qwen3-4B-Q8_0.gguf"

# Russian Piper voice (female, medium)
curl -L \
  "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx?download=true" \
  -o "$PROJECT_ROOT/data/models/tts/ru_RU-irina-medium.onnx"

curl -L \
  "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx.json?download=true" \
  -o "$PROJECT_ROOT/data/models/tts/ru_RU-irina-medium.onnx.json"

# Pre-download faster-whisper "small" model into HF cache
source "$PROJECT_ROOT/.venv/bin/activate"
python - <<'PY'
from faster_whisper import WhisperModel

print("Downloading faster-whisper model: small / int8 (cache only)")
WhisperModel("small", device="cpu", compute_type="int8")
print("Done.")
PY

echo "Model download complete."
