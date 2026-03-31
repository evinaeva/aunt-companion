# Gosha MVP — Overview

## Goal

Build the smallest useful self-hosted Telegram companion for **1–3 whitelisted users**.

The MVP exists only to answer one question:

> Is it pleasant and convenient to talk to Gosha in Russian by text and voice?

## In scope

- Telegram bot with **long polling**
- Text input
- Voice input
- Text output
- Voice output
- Basic persistent memory
- Per-user isolation
- Local CPU-only LLM
- Local STT
- Local TTS
- SQLite as the only database

## Out of scope

- Web search
- Weather
- Books
- Music
- Transport
- Admin panel
- Vector DB
- Semantic embeddings
- FastAPI
- Docker-first deployment
- Webhook mode

## Design principles

1. **Smallest useful system first**
2. **One process for the bot, one process for llama.cpp**
3. **SQLite is the source of truth**
4. **Every memory query is filtered by user_id**
5. **Russian UX first**
6. **Short responses by default**
7. **No hidden magic**

## Recommended runtime choices

- Python app: `aiogram` + `aiosqlite`
- Local LLM runtime: `llama.cpp` HTTP server
- Local LLM model: `Qwen3-4B` GGUF
- STT: `faster-whisper` with `small` and `int8`
- TTS: `piper-tts` with one Russian voice
- Audio helper: `ffmpeg`

## MVP success criteria

The MVP is successful if all of the following are true:

- The user can send text and receive a sensible Russian reply.
- The user can send a voice message and receive a sensible reply.
- The bot can reply with a voice message.
- The bot remembers at least a few stable personal facts between days.
- No user can access another user’s memory.
- Median text turnaround feels acceptable on CPU-only hardware.
