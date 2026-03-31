# Gosha MVP kit

Gosha is a self-hosted Russian-language Telegram companion focused on **text chat first** for a tiny allowlist (1–3 users).

This repository currently provides:
- Telegram polling bot with allowlist middleware
- Local SQLite initialization and repositories
- Local llama.cpp HTTP client integration for replies
- Ubuntu/server scripts and systemd templates
- Tests for config, DB behavior, and text-chat wiring

## Current scope (implemented)

- `/start` and `/help` commands
- Text input -> text output flow
- User creation and message persistence in SQLite
- Local llama.cpp request path with fallback message on LLM failures
- Basic operational scripts for bootstrap/run/smoke checks

## Not implemented yet

- Memory-writing behavior used in reply flow
- Voice/STT/TTS runtime path in production bot flow
- FastAPI/web services, tools, books, web search, or other feature expansions

## Quick local run

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e '.[dev]'
cp .env.example .env
pytest
./scripts/05_run_bot.sh "$(pwd)"
```

## Local smoke check

```bash
./scripts/07_smoke_check.sh "$(pwd)"
```

## Ubuntu smoke path

```bash
chmod +x scripts/*.sh
./scripts/01_bootstrap_ubuntu.sh /srv/gosha
./scripts/03_create_env.sh /srv/gosha
nano /srv/gosha/.env
./scripts/07_smoke_check.sh /srv/gosha
```

See `docs/server-quickstart.md` and `docs/operations.md` for server operations.
