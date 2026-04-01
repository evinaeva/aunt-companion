"""Text-to-speech adapters for Telegram voice pipeline."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from app.config import TTSSettings


class TTSAdapter(Protocol):
    async def synthesize(self, text: str) -> str:
        """Synthesize TTS output and return path to OGG/OGA voice file."""


class PiperTTSAdapter:
    def __init__(self, *, voice_path: Path, output_dir: Path) -> None:
        self.voice_path = voice_path
        self.output_dir = output_dir

    async def synthesize(self, text: str) -> str:
        if shutil.which("piper") is None:
            raise RuntimeError("piper binary not found")
        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg binary not found")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        base_name = f"gosha-tts-{uuid4().hex}"
        wav_path = self.output_dir / f"{base_name}.wav"
        ogg_path = self.output_dir / f"{base_name}.ogg"

        proc = await asyncio.create_subprocess_exec(
            "piper",
            "--model",
            str(self.voice_path),
            "--output_file",
            str(wav_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate(input=text.encode("utf-8"))
        if proc.returncode != 0:
            raise RuntimeError(f"Piper failed: {stderr.decode('utf-8', errors='ignore')}")

        ffmpeg = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-i",
            str(wav_path),
            "-c:a",
            "libopus",
            "-b:a",
            "24k",
            str(ogg_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, ffmpeg_err = await ffmpeg.communicate()
        if ffmpeg.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {ffmpeg_err.decode('utf-8', errors='ignore')}")
        return str(ogg_path)


class UnavailableTTSAdapter:
    async def synthesize(self, text: str) -> str:
        raise RuntimeError("TTS unavailable")


def build_tts_adapter(settings: TTSSettings, *, output_dir: Path) -> TTSAdapter:
    if settings.provider == "piper":
        return PiperTTSAdapter(voice_path=settings.piper_voice_path, output_dir=output_dir)
    return UnavailableTTSAdapter()
