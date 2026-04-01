"""Helpers for building compact LLM prompts for text chat."""

from __future__ import annotations

from pathlib import Path

from app.db import Message

PROMPT_FILE_PATH = Path(__file__).resolve().parents[2] / "prompts" / "system_prompt_ru.txt"


def load_system_prompt_ru() -> str:
    """Load the canonical Russian system prompt independent of current working directory."""
    return PROMPT_FILE_PATH.read_text(encoding="utf-8").strip()


def build_chat_messages(
    *,
    system_prompt: str,
    target_user_id: int,
    recent_messages: list[Message],
    current_user_text: str,
) -> list[dict[str, str]]:
    """Build a compact OpenAI-style messages list for llama.cpp."""
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt.strip()}]

    same_user_messages = [item for item in recent_messages if item.user_id == target_user_id]
    for message in reversed(same_user_messages):
        role = "user" if message.direction == "incoming" else "assistant"
        messages.append({"role": role, "content": message.text.strip()})

    messages.append({"role": "user", "content": current_user_text.strip()})
    return messages
