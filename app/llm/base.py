"""Shared provider-agnostic LLM abstractions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Protocol


@dataclass(slots=True)
class LLMResponse:
    """Structured LLM result returned by adapters."""

    text: str
    is_fallback: bool = False
    raw: Any | None = None


class LLMAdapter(Protocol):
    """Provider-agnostic interface consumed by Telegram handlers."""

    async def generate(self, messages: list[dict[str, str]]) -> LLMResponse:
        """Generate an assistant reply for chat messages."""


class ChatClient(LLMAdapter, Protocol):
    """Backward-compatible alias for handlers and tests."""

    async def generate_reply(self, messages: list[dict[str, str]]) -> str:
        """Generate a short assistant reply for legacy callers."""
