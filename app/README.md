# App Skeleton

This directory is intentionally minimal.
Codex CLI should implement the MVP here following:

- `docs/SPEC-001-gosha-mvp.md`
- `docs/architecture.md`
- `contract/companion_contract_v1.md`
- `codex/codex_cli_prompt.md`

Suggested first files:
- `app/main.py`
- `app/config.py`
- `app/telegram/bot.py`
- `app/telegram/routers/chat.py`
- `app/telegram/routers/voice.py`
- `app/domain/services/conversation_service.py`
- `app/domain/services/memory_service.py`
- `app/db/sqlite.py`
- `app/db/repositories/messages.py`
- `app/db/repositories/users.py`
- `app/llm/client.py`
- `app/stt/faster_whisper_engine.py`
- `app/tts/piper_engine.py`
- `app/jobs/daily_summary_job.py`
