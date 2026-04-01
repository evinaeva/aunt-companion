"""Text-to-speech adapters for Telegram voice pipeline."""

from __future__ import annotations

import asyncio
from typing import Protocol

from app.config import TTSSettings


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
    ) -> None:
        self.language_code = language_code
        self.voice_name = voice_name
        self.voice_gender = voice_gender
        self.audio_encoding = audio_encoding

    async def synthesize(self, text: str) -> bytes:
        def _run() -> bytes:
            from google.cloud import texttospeech

            client = texttospeech.TextToSpeechClient()
            request_input = texttospeech.SynthesisInput(text=text)

            if self.voice_name:
                voice = texttospeech.VoiceSelectionParams(
                    language_code=self.language_code,
                    name=self.voice_name,
                )
            else:
                voice = texttospeech.VoiceSelectionParams(
                    language_code=self.language_code,
                    ssml_gender=texttospeech.SsmlVoiceGender[self.voice_gender.upper()],
                )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding[self.audio_encoding.upper()],
            )
            response = client.synthesize_speech(input=request_input, voice=voice, audio_config=audio_config)
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
        )
    return UnavailableTTSAdapter()
