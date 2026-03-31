# Gosha MVP — Implementation Contract v1

This contract is the **source of truth** for Codex and for all future code in this repository.

## 1. Scope

The implementation target is a **minimal Telegram companion MVP** with:
- text chat
- voice input
- voice output
- persistent memory
- strict per-user isolation

Everything outside this scope is explicitly deferred.

## 2. Out of scope

Do **not** implement in v1:
- web search
- books
- music
- weather
- transport
- embeddings
- vector DB
- semantic search
- FastAPI
- webhook mode
- Docker-only setup
- admin web UI
- external paid APIs

## 3. Canonical stack

- Python app framework: `aiogram`
- Local LLM runtime: `llama.cpp` HTTP server
- Local model family: `Qwen3-4B` GGUF
- STT: `faster-whisper`
- TTS: `piper-tts`
- DB: SQLite
- Audio utility: `ffmpeg`

## 4. Canonical runtime architecture

There are only **two runtime services** in v1:

1. `gosha-llama`
2. `gosha-bot`

No third application service may be introduced without changing this contract.

## 5. User isolation invariants

These are hard requirements.

1. Each incoming Telegram update must resolve to exactly one `user_id`.
2. Every DB query that touches user-owned data must include `user_id`.
3. No retrieval over all users is allowed for conversational context.
4. Unknown Telegram users must be rejected.
5. Admin status must never bypass user memory isolation.
6. Messages, facts and summaries are owned by exactly one user.

## 6. Behavioral contract

### Assistant behavior
- Replies must be primarily in Russian.
- Tone must be simple, warm and concise.
- Default replies must be short.
- The assistant must not invent personal facts.
- The assistant must distinguish memory from current user input.
- If uncertain, the assistant should say it is not sure.

### Voice behavior
- Voice replies are short by default.
- If synthesis fails, the bot falls back to text.
- If transcription fails, the bot asks the user to repeat more clearly.

## 7. Persistence contract

SQLite is the source of truth.

Required tables:
- `users`
- `user_settings`
- `messages`
- `profile_facts`
- `daily_summaries`

### SQLite rules
- enable WAL mode
- configure busy timeout
- keep write transactions short
- no ORM is required
- simple SQL or `aiosqlite` is preferred

## 8. Memory contract

### Required memory in v1
- recent messages
- profile facts
- rolling summary

### Retrieval order
1. system prompt
2. profile facts
3. rolling summary
4. recent messages
5. current input

### Write policy
- write message history for every turn
- update profile facts only with high confidence
- update rolling summary periodically, not necessarily on every turn

## 9. Telegram contract

Required commands:
- `/start`
- `/help`
- `/voice_on`
- `/voice_off`
- `/whoami`
- `/memory`

Telegram mode:
- long polling only

## 10. LLM contract

The LLM endpoint is a **local** llama.cpp-compatible HTTP server.

The bot code must:
- read base URL from environment
- read model identifier from environment
- support short generation settings
- avoid giant contexts
- keep prompts deterministic and readable

## 11. STT contract

The STT adapter must:
- accept Telegram voice input
- save to temp directory
- transcribe with `faster-whisper`
- support CPU mode
- use a configurable model size
- default to `small` with `int8`

## 12. TTS contract

The TTS adapter must:
- accept plain text
- synthesize using Piper
- use one configured Russian voice model
- return audio that can be sent back to Telegram

## 13. Filesystem contract

Canonical directories:
- `data/db/`
- `data/models/llm/`
- `data/models/tts/`
- `data/cache/`
- `data/tmp/`
- `data/logs/`

The bot may write only inside project-owned data directories.

## 14. Configuration contract

All secrets and runtime options must come from environment variables or `.env`.

Never hard-code:
- bot token
- Telegram IDs
- model paths
- service URLs

## 15. Testing contract

At minimum, add tests for:
- user isolation
- memory retrieval order
- voice pipeline happy path

## 16. Acceptance criteria

The MVP is accepted only when all items are true:

1. whitelisted user can text the bot and get a Russian reply
2. whitelisted user can send a voice note and get a reply
3. reply can be voice when voice mode is enabled
4. profile facts survive restart
5. one user cannot retrieve another user’s data
6. app starts and restarts under `systemd`

## 17. Change policy

If implementation needs any of the following, the contract must be updated first:
- new network service
- new database engine
- vector retrieval
- hosted third-party model APIs
- web UI
- broader feature scope
