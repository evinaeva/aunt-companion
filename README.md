# Gosha MVP kit

Gosha is a self-hosted Russian-language Telegram companion focused on **text chat first** for a tiny allowlist (1–3 users).

This repository currently provides:
- Telegram polling bot with allowlist middleware
- Local SQLite initialization and repositories
- Gemini API integration (default) with optional local llama.cpp backend
- Ubuntu/server scripts and systemd templates
- Tests for config, DB behavior, and text-chat wiring

## Current scope (implemented)

- `/start` and `/help` commands
- Text input -> text output flow
- User creation and message persistence in SQLite
- Gemini `gemini-2.5-flash-lite` request path (default) with optional llama.cpp secondary backend
- Basic operational scripts for bootstrap/run/smoke checks

## Not implemented yet

- Memory-writing behavior used in reply flow
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


## LLM configuration

Preferred runtime config is `config/llm.local.toml` (copy from `config/llm.example.toml`). Telegram chat always uses `[primary]`.
Use Gemini in `[primary]` (`gemini-2.5-flash-lite`) and keep local llama.cpp in `[secondary]` for optional/manual use.
There is currently no automatic runtime failover from `[primary]` to `[secondary]`.
If `config/llm.local.toml` is missing, app falls back to `.env` (`LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_API_KEY`).
If `config/llm.local.toml` exists with Gemini placeholder key material, startup fails fast with a clear error.
