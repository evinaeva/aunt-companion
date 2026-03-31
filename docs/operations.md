# Gosha MVP — Operations

## Start manually

### LLM server
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
- `gosha-llama` service status/logs
- `LLM_BASE_URL` in `.env`
- local port/firewall policy
