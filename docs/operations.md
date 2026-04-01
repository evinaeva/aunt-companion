# Gosha MVP — Operations

## Start manually

### LLM (default Gemini, optional local llama.cpp)
Telegram chat uses only `[primary]` from `config/llm.local.toml`.
Set Gemini credentials in `[primary]` (`gemini-2.5-flash-lite`).
`[secondary]` is stored for optional/manual use and has no automatic runtime failover.
If `config/llm.local.toml` is absent, runtime falls back to `.env` (`LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`).

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
- `config/llm.local.toml` does not contain placeholder Gemini API key (`YOUR_GEMINI_API_KEY`)
- if using local llama as secondary: `gosha-llama` service status/logs and local port/firewall
- fallback `.env` values (`LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`)
