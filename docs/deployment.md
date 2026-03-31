# Gosha MVP — Deployment

## Target

Single Ubuntu server, CPU-only.

## Runtime layout

- `llama.cpp` server on `127.0.0.1:8012`
- Telegram bot Python app in one process
- local filesystem for DB, logs, models and temp files
- `systemd` for autostart

## Recommended directories

- project root: `/srv/gosha`
- database: `/srv/gosha/data/db/gosha.sqlite3`
- logs: `/srv/gosha/data/logs/`
- LLM models: `/srv/gosha/data/models/llm/`
- TTS voices: `/srv/gosha/data/models/tts/`
- temp audio: `/srv/gosha/data/tmp/`
- Hugging Face cache: `/srv/gosha/data/cache/huggingface/`

## Ports

- `8012` — llama.cpp
- no public HTTP endpoint required for MVP

## Services

### gosha-llama.service
Starts local LLM server.

### gosha-bot.service
Starts Telegram bot.

## Boot order

1. `gosha-llama.service`
2. `gosha-bot.service`

## Operational constraints

- keep context size moderate
- keep assistant replies short
- keep voice replies short
- set SQLite WAL mode
- do not run both services as root in production
