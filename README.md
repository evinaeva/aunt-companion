# Gosha MVP kit

This archive contains a minimal repo-oriented documentation set for **Gosha**, a Russian-language Telegram companion MVP.

Included:
- `docs/` — project docs
- `contract/` — implementation contract and JSON schemas
- `codex/` — detailed Codex CLI prompt
- `scripts/` — Ubuntu bootstrap and model download scripts
- `deploy/systemd/` — systemd service templates
- `.env.example` — environment template
- `prompts/system_prompt_ru.txt` — starter system prompt

## Run (Phase 1 skeleton)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e '.[dev]'
cp .env.example .env
pytest
python -m app.main
```

Phase 1 currently initializes configuration and logging only.
