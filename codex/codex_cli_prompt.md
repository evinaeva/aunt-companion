# Codex CLI prompt for Gosha MVP

Use the text below as the starting prompt in Codex CLI.

---

You are implementing a **minimal self-hosted Telegram companion MVP** called **Gosha**.

Read these files first and treat them as the source of truth:
- `docs/SPEC-001-gosha-mvp.md`
- `docs/overview.md`
- `docs/architecture.md`
- `docs/memory-model.md`
- `contract/companion_contract_v1.md`

## Your mission

Build the **smallest working MVP** that satisfies the contract.

The MVP must support only:
- Telegram long polling
- whitelisted users
- text input
- voice input
- text output
- voice output
- persistent per-user memory
- Russian-first conversation

Do **not** implement:
- web search
- weather
- books
- music
- transport
- FastAPI
- webhook mode
- vector DB
- embeddings
- semantic retrieval
- Docker-only deployment
- admin web UI

## Implementation rules

- Use **Python** with **aiogram**.
- Use **SQLite** as the only database.
- Use **aiosqlite** or direct SQL; no heavyweight ORM.
- Use **llama.cpp HTTP server** as the local LLM endpoint.
- Use **faster-whisper** for STT.
- Use **piper-tts** for TTS.
- Use **ffmpeg** for audio conversion where needed.
- Keep the architecture small and readable.
- Prefer a single bot process plus an external llama.cpp service.
- Keep replies short by default.
- Keep all assistant-facing UX in Russian.
- Keep prompts explicit and readable.
- Put all secrets and runtime config in `.env`.

## User isolation rules

These are critical and must be enforced in code and tests:
- map every Telegram update to a single internal `user_id`
- every memory read/write must be filtered by `user_id`
- no cross-user retrieval under any code path
- reject unknown Telegram users unless they are explicitly whitelisted

## Minimum deliverables

1. Project skeleton under the documented layout.
2. `.env.example`
3. SQLite bootstrap/migration logic.
4. Telegram bot with required commands:
   - `/start`
   - `/help`
   - `/voice_on`
   - `/voice_off`
   - `/whoami`
   - `/memory`
5. Text chat flow.
6. Voice input flow:
   - download Telegram voice message
   - transcribe with faster-whisper
   - feed transcript into normal chat flow
7. Voice output flow:
   - synthesize short response with Piper
   - send as Telegram audio/voice
   - fall back to text on failure
8. Minimal memory system:
   - recent messages
   - profile facts
   - rolling summary
9. Tests for:
   - user isolation
   - memory retrieval order
   - happy-path voice pipeline
10. README quickstart.

## Recommended code structure

Use a simple structure like:
- `app/config.py`
- `app/db.py`
- `app/models.py`
- `app/bot.py`
- `app/handlers.py`
- `app/llm.py`
- `app/stt.py`
- `app/tts.py`
- `app/memory.py`
- `app/main.py`

Do not over-split the code into many tiny files.

## Data model

Implement at least these tables:
- `users`
- `user_settings`
- `messages`
- `profile_facts`
- `daily_summaries`

Use SQLite WAL mode and a busy timeout.

## LLM behavior requirements

- The assistant must answer in Russian by default.
- The tone must be warm, simple and concise.
- The assistant must not invent personal facts.
- The assistant should admit uncertainty.
- The system prompt must explicitly distinguish:
  - stable facts from memory
  - recent conversation context
  - current user input

## Memory implementation guidance

Implement only a lightweight retrieval stack:
- profile facts
- one rolling summary
- last 10–12 messages

Do not build FTS, RAG, embeddings, vector DB or anything fancy in this MVP.

A pragmatic approach is acceptable:
- update recent messages every turn
- upsert profile facts when confidence is high
- update the rolling summary periodically or after a small batch of turns

## Environment variables

Support environment variables for:
- `TELEGRAM_BOT_TOKEN`
- `ALLOWED_TELEGRAM_USER_IDS`
- `ADMIN_TELEGRAM_USER_ID`
- `SQLITE_PATH`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `LLM_CONTEXT_SIZE`
- `LLM_MAX_TOKENS`
- `LLM_TEMPERATURE`
- `STT_MODEL_SIZE`
- `TTS_VOICE_MODEL_PATH`
- `TTS_VOICE_CONFIG_PATH`
- `TEMP_DIR`
- `LOG_LEVEL`

## Quality bar

- deliver working code, not just TODOs
- prefer clarity over cleverness
- add type hints
- include useful logging
- fail loudly, not silently
- keep functions focused
- keep comments practical
- do not introduce speculative abstractions

## Execution style

Act autonomously and finish as much as possible in one pass.
Do not stop at planning.
Do not ask for clarification unless completely blocked by missing repository files or secrets.
Read the existing docs and contract first, then implement code, tests, and README updates.

At the end:
- summarize what you changed
- list any assumptions
- list exact commands to run the bot locally on Ubuntu
