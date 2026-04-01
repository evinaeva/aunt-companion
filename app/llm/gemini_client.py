"""Minimal Gemini Developer API adapter for text generation."""

from __future__ import annotations

import asyncio

from google import genai
from google.genai import types


class GeminiClient:
    """Tiny adapter around google-genai for text-only replies."""

    def __init__(self, *, api_key: str, model: str, base_url: str, timeout_seconds: float = 30.0) -> None:
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(base_url=base_url, timeout=self.timeout_seconds * 1000),
        )

    async def generate_reply(self, messages: list[dict[str, str]]) -> str:
        system_instruction = ""
        conversation_lines: list[str] = []

        for message in messages:
            role = message.get("role", "user")
            content = (message.get("content") or "").strip()
            if not content:
                continue
            if role == "system":
                system_instruction = content
                continue
            label = "Пользователь" if role == "user" else "Ассистент"
            conversation_lines.append(f"{label}: {content}")

        prompt = "\n".join(conversation_lines).strip()
        if not prompt:
            prompt = "Пользователь: Ответь коротко и по делу."

        def _request() -> str:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction or None,
                    temperature=0.4,
                    max_output_tokens=180,
                ),
            )
            text = getattr(response, "text", None)
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Missing text content in Gemini response")
            return text.strip()

        return await asyncio.to_thread(_request)
