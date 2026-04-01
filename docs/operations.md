# Gosha MVP — Operations

## Start manually

### LLM (default Gemini, optional local llama.cpp)
For default Telegram chat, set Gemini credentials in `config/llm.local.toml` (`gemini-2.5-flash-lite`).

Optional local llama server (secondary backend):
```bash
cd /srv/gosha
./scripts/04_start_llama_server.sh /srv/gosha
```

### Bot
```bash
cd /srv/gosha
./scripts/05_run_bot.sh /srv/gosha
```

## Basic smoke check

```bash
cd /srv/gosha
./scripts/07_smoke_check.sh /srv/gosha
```

## Logs

With systemd:
```bash
journalctl -u gosha-llama -f
journalctl -u gosha-bot -f
```

## SQLite checks

```bash
sqlite3 /srv/gosha/data/db/gosha.sqlite3 "PRAGMA journal_mode;"
sqlite3 /srv/gosha/data/db/gosha.sqlite3 "PRAGMA integrity_check;"
```

## Common failures

### 1. Telegram replies stop
Check:
- bot token
- allowed Telegram IDs
- `gosha-bot` service logs

### 2. LLM not reachable
Check:
- `config/llm.local.toml` `[primary]` values (Gemini model `gemini-2.5-flash-lite`, API key, base URL)
- if using local llama as secondary: `gosha-llama` service status/logs and local port/firewall
- fallback `.env` values (`LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`)
