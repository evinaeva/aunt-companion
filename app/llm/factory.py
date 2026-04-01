"""LLM client factory based on resolved settings."""

from __future__ import annotations

from app.config import Settings
from app.llm.base import ChatClient
from app.llm.client import LlamaClient
from app.llm.gemini_client import GeminiClient


def build_primary_chat_client(settings: Settings) -> ChatClient:
    """Create a chat client from preferred runtime LLM settings."""
    llm = settings.llm
    if llm.provider == "gemini":
        if not llm.api_key:
            raise ValueError("Gemini provider requires api_key")
        return GeminiClient(api_key=llm.api_key, model=llm.model, base_url=llm.base_url)

    if llm.provider == "llama_cpp":
        return LlamaClient(base_url=llm.base_url, model=llm.model)

    raise ValueError(f"Unsupported primary provider: {llm.provider}")
