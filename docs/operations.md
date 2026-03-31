# Gosha MVP — Operations

## Start manually

### LLM server
```bash
cd /srv/gosha
./scripts/04_start_llama_server.sh
```

### Bot
```bash
cd /srv/gosha
./scripts/05_run_bot.sh
```

## Logs

Recommended files:
- `/srv/gosha/data/logs/llama.log`
- `/srv/gosha/data/logs/bot.log`

When using systemd:
```bash
journalctl -u gosha-llama -f
journalctl -u gosha-bot -f
```

## SQLite maintenance

Use:
- WAL mode
- busy timeout
- one short write transaction per operation

Basic checks:
```bash
sqlite3 /srv/gosha/data/db/gosha.sqlite3 "PRAGMA journal_mode;"
sqlite3 /srv/gosha/data/db/gosha.sqlite3 "PRAGMA integrity_check;"
```

## Backup

MVP backup can stay very simple:
```bash
mkdir -p /srv/gosha/data/backups
sqlite3 /srv/gosha/data/db/gosha.sqlite3 ".backup '/srv/gosha/data/backups/gosha-$(date +%F).sqlite3'"
```

## Common failures

### 1. Telegram replies stop
Check:
- bot token
- allowed Telegram IDs
- polling loop logs

### 2. Voice transcription fails
Check:
- `ffmpeg`
- faster-whisper model cache
- temp directory permissions

### 3. TTS fails
Check:
- Piper voice `.onnx` and `.onnx.json` exist
- selected voice path in `.env`
- write permissions for temp/output files

### 4. LLM is too slow
Mitigations:
- switch from `Q8_0` to `Q5_K_M`
- reduce context
- reduce max tokens
- shorten system prompt
