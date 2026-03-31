# Gosha MVP — Overview

## Goal

Run a small, reliable self-hosted Telegram companion for **1–3 whitelisted users** on Ubuntu.

## Current implemented scope

- Telegram bot with **long polling**
- Text input
- Text output
- SQLite persistence for users/messages/conversations
- Local llama.cpp call path for text generation
- Allowlist access control

## Planned but not implemented in runtime flow yet

- Voice input/output runtime path
- Memory extraction/writing integrated into replies
- Additional user-facing commands beyond `/start` and `/help`

## Out of scope for this phase

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
