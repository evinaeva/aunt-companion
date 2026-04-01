"""Speech-to-text adapters for Telegram voice pipeline."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Protocol

from app.config import STTSettings


class STTAdapter(Protocol):
    async def transcribe(self, file_path: str) -> str:
        """Transcribe WAV file into plain text."""


class FasterWhisperAdapter:
    def __init__(self, *, model_size: str, compute_type: str) -> None:
        self.model_size = model_size
        self.compute_type = compute_type
        self._model = None

    async def transcribe(self, file_path: str) -> str:
        def _run() -> str:
            if self._model is None:
                from faster_whisper import WhisperModel

                self._model = WhisperModel(self.model_size, compute_type=self.compute_type)
            segments, _ = self._model.transcribe(file_path)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            if not text:
                raise ValueError("Empty transcript")
            return text

        return await asyncio.to_thread(_run)


class UnavailableSTTAdapter:
    async def transcribe(self, file_path: str) -> str:
        raise RuntimeError(f"STT unavailable for file: {Path(file_path).name}")


def build_stt_adapter(settings: STTSettings) -> STTAdapter:
    if settings.provider == "faster_whisper":
        return FasterWhisperAdapter(model_size=settings.model_size, compute_type=settings.compute_type)
    return UnavailableSTTAdapter()
