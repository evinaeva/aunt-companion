# Gosha MVP — Memory Model

## Goal

Provide just enough memory so the bot feels personal, without adding complex retrieval infrastructure.

## Memory types

### A. Recent conversation window
- last 10–12 messages for this user
- always loaded
- highest priority

### B. Profile facts
Structured stable facts, for example:
- preferred name
- relatives
- favorite topics
- prefers voice replies
- city / timezone if user explicitly said it

### C. Rolling summary
One short summary per user, updated occasionally.
Purpose:
- compress older dialogue
- keep stable context across days

## What not to store as profile facts

Do not store:
- guesses
- medical claims
- secrets not relevant to future conversation
- one-off noisy statements
- facts with low confidence

## Retrieval order

Before every response, assemble context in this order:
1. system prompt
2. user profile facts
3. rolling summary
4. recent messages
5. current user input

## Recommended extraction strategy

Keep extraction simple:
- after each assistant response, optionally run a small structured extraction step
- only write a fact if confidence is high
- upsert by `(user_id, fact_key)`

## Minimal tables

### users
- id
- telegram_user_id
- display_name
- is_admin
- is_active
- created_at

### user_settings
- user_id
- reply_mode (`text`, `voice`)
- tts_voice
- language_code
- updated_at

### messages
- id
- user_id
- direction (`incoming`, `outgoing`)
- input_type (`text`, `voice`, `command`)
- text
- telegram_message_id
- created_at

### profile_facts
- id
- user_id
- fact_key
- fact_value
- confidence
- source_message_id
- updated_at

### daily_summaries
- id
- user_id
- summary_text
- source_message_range_start
- source_message_range_end
- updated_at

## Hard rules

- Every read/write must include `user_id`.
- No shared conversational memory between users.
- No global retrieval over all messages.
- The model must never be told another user’s facts.
