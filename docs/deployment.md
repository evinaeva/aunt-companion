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
- logs: use `journalctl` for systemd services
- LLM models: `/srv/gosha/data/models/llm/`
- TTS voices: `/srv/gosha/data/models/tts/` (for future voice phase)
- temp files: `/srv/gosha/data/tmp/`

## Services

### gosha-llama.service
Starts local llama.cpp server using `scripts/04_start_llama_server.sh`.

### gosha-bot.service
Starts Telegram bot using `scripts/05_run_bot.sh`.

## Boot order

1. `gosha-llama.service`
2. `gosha-bot.service`

## Notes

- Services use `EnvironmentFile=/srv/gosha/.env`.
- Use non-root service user in production.
