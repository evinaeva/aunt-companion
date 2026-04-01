"""Shared LLM client protocol."""

from __future__ import annotations

from typing import Protocol


class ChatClient(Protocol):
    """Minimal interface required by Telegram text handlers."""

    async def generate_reply(self, messages: list[dict[str, str]]) -> str:
        """Generate a short assistant reply for chat messages."""
