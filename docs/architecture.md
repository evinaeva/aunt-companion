# Gosha MVP — Architecture (current)

## Runtime components in use

1. Telegram (`aiogram`) long-polling bot process
2. SQLite database (`aiosqlite`) for persistence
3. Local llama.cpp HTTP server for text completions

## Current text message flow

1. Telegram update arrives in polling loop.
2. Allowlist middleware checks `from_user.id`.
3. User/conversation/message records are loaded/saved in SQLite.
4. Prompt is built from recent messages for that same `user_id` only.
5. LLM reply is requested from local llama.cpp endpoint.
6. Reply is saved and sent back to Telegram.

## Operational properties

- SQLite WAL + busy timeout are enabled at connect time.
- Runtime directories are created on startup.
- Non-whitelisted users are rejected.
- LLM failures return a graceful fallback response.

## Deferred architecture elements (not active yet)

- Voice pipeline (STT/TTS)
- Memory extraction and summary jobs in bot runtime
