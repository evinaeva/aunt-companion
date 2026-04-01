"""llama.cpp HTTP adapter for provider-agnostic text generation."""

from __future__ import annotations

from typing import Any

import httpx

from app.llm.base import LLMResponse


class LlamaCppAdapter:
    """Tiny async client targeting llama.cpp OpenAI-compatible endpoint."""

    def __init__(self, *, base_url: str, model: str, timeout_seconds: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def generate(self, messages: list[dict[str, str]]) -> LLMResponse:
        """Request a concise response from local llama.cpp server."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 180,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/v1/chat/completions", json=payload)
            response.raise_for_status()
            body = response.json()

        choices = body.get("choices")
        if not choices:
            raise ValueError("Missing 'choices' in llama.cpp response")

        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str):
            raise ValueError("Missing assistant text content in llama.cpp response")

        return LLMResponse(text=content.strip(), is_fallback=False, raw=body)

    async def generate_reply(self, messages: list[dict[str, str]]) -> str:
        """Backward-compatible helper for text-only callers."""
        response = await self.generate(messages)
        return response.text


LlamaClient = LlamaCppAdapter
