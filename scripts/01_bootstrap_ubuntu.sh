#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-/srv/gosha}"

sudo apt-get update
sudo apt-get install -y \
  git \
  curl \
  wget \
  unzip \
  build-essential \
  cmake \
  pkg-config \
  ffmpeg \
  sqlite3 \
  libsqlite3-dev \
  libopenblas-dev \
  python3 \
  python3-venv \
  python3-pip

mkdir -p "$PROJECT_ROOT"
cd "$PROJECT_ROOT"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

# Python dependencies for MVP
pip install \
  "aiogram==3.26.0" \
  "aiosqlite>=0.20,<1.0" \
  "faster-whisper" \
  "piper-tts==1.4.1" \
  "httpx>=0.28,<1.0" \
  "pydantic>=2.8,<3.0" \
  "pydantic-settings>=2.4,<3.0" \
  "python-dotenv>=1.0,<2.0" \
  "orjson>=3.10,<4.0" \
  "pytest>=8.0,<9.0" \
  "pytest-asyncio>=0.23,<1.0" \
  "ruff>=0.6,<1.0"

# Build llama.cpp
mkdir -p "$PROJECT_ROOT/vendor"
if [ ! -d "$PROJECT_ROOT/vendor/llama.cpp" ]; then
  git clone https://github.com/ggml-org/llama.cpp.git "$PROJECT_ROOT/vendor/llama.cpp"
fi

cmake -S "$PROJECT_ROOT/vendor/llama.cpp" \
      -B "$PROJECT_ROOT/vendor/llama.cpp/build" \
      -DGGML_BLAS=ON \
      -DGGML_BLAS_VENDOR=OpenBLAS

cmake --build "$PROJECT_ROOT/vendor/llama.cpp/build" --config Release -j"$(nproc)"

echo "Bootstrap complete."
