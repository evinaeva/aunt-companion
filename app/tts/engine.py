"""Text-to-speech adapters for Telegram voice pipeline."""

from __future__ import annotations

import asyncio
from threading import Lock
from typing import TYPE_CHECKING, Protocol

from app.config import TTSSettings

if TYPE_CHECKING:
    from google.cloud import texttospeech


class TTSAdapter(Protocol):
    async def synthesize(self, text: str) -> bytes:
        """Synthesize TTS output and return OGG/OGA bytes."""


class GoogleCloudTTSAdapter:
    def __init__(
        self,
        *,
        language_code: str,
        voice_name: str,
        voice_gender: str,
        audio_encoding: str,
        timeout_seconds: float,
    ) -> None:
        self.language_code = language_code
        self.voice_name = voice_name
        self.voice_gender = voice_gender
        self.audio_encoding = audio_encoding
        self.timeout_seconds = timeout_seconds
        self._client: texttospeech.TextToSpeechClient | None = None
        self._client_lock = Lock()

    def _get_client(self) -> texttospeech.TextToSpeechClient:
        from google.cloud import texttospeech

        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    self._client = texttospeech.TextToSpeechClient()
        return self._client

    async def synthesize(self, text: str) -> bytes:
        def _run() -> bytes:
            from google.cloud import texttospeech

            client = self._get_client()
            request_input = texttospeech.SynthesisInput(text=text)

            if self.voice_name:
                voice = texttospeech.VoiceSelectionParams(
                    language_code=self.language_code,
                    name=self.voice_name,
                )
            else:
                voice = texttospeech.VoiceSelectionParams(
                    language_code=self.language_code,
                    ssml_gender=texttospeech.SsmlVoiceGender[self.voice_gender],
                )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding[self.audio_encoding],
            )
            response = client.synthesize_speech(
                input=request_input,
                voice=voice,
                audio_config=audio_config,
                timeout=self.timeout_seconds,
            )
            return bytes(response.audio_content)

        return await asyncio.to_thread(_run)


class UnavailableTTSAdapter:
    async def synthesize(self, text: str) -> bytes:
        raise RuntimeError("TTS unavailable")


def build_tts_adapter(settings: TTSSettings) -> TTSAdapter:
    if settings.provider == "google_cloud":
        return GoogleCloudTTSAdapter(
            language_code=settings.language_code,
            voice_name=settings.voice_name,
            voice_gender=settings.voice_gender,
            audio_encoding=settings.audio_encoding,
            timeout_seconds=settings.timeout_seconds,
        )
    return UnavailableTTSAdapter()
