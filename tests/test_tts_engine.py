import sys
from types import ModuleType, SimpleNamespace

import pytest

from app.config.settings import TTSSettings
from app.tts.engine import GoogleCloudTTSAdapter


@pytest.mark.asyncio
async def test_google_tts_adapter_reuses_client_and_passes_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    call_log: dict[str, object] = {"client_inits": 0, "timeouts": []}

    class FakeClient:
        def __init__(self) -> None:
            call_log["client_inits"] = int(call_log["client_inits"]) + 1

        def synthesize_speech(self, *, input, voice, audio_config, timeout):
            assert input.text
            assert voice.language_code == "ru-RU"
            assert audio_config.audio_encoding == "OGG_OPUS"
            timeouts = list(call_log["timeouts"])
            timeouts.append(timeout)
            call_log["timeouts"] = timeouts
            return SimpleNamespace(audio_content=b"opus-bytes")

    class FakeSynthesisInput:
        def __init__(self, *, text: str):
            self.text = text

    class FakeVoiceSelectionParams:
        def __init__(self, *, language_code: str, name: str | None = None, ssml_gender: str | None = None):
            self.language_code = language_code
            self.name = name
            self.ssml_gender = ssml_gender

    class FakeAudioConfig:
        def __init__(self, *, audio_encoding: str):
            self.audio_encoding = audio_encoding

    fake_tts = ModuleType("google.cloud.texttospeech")
    fake_tts.TextToSpeechClient = FakeClient
    fake_tts.SynthesisInput = FakeSynthesisInput
    fake_tts.VoiceSelectionParams = FakeVoiceSelectionParams
    fake_tts.AudioConfig = FakeAudioConfig
    fake_tts.SsmlVoiceGender = {
        "SSML_VOICE_GENDER_UNSPECIFIED": "SSML_VOICE_GENDER_UNSPECIFIED",
        "MALE": "MALE",
        "FEMALE": "FEMALE",
        "NEUTRAL": "NEUTRAL",
    }
    fake_tts.AudioEncoding = {
        "LINEAR16": "LINEAR16",
        "MP3": "MP3",
        "OGG_OPUS": "OGG_OPUS",
        "MULAW": "MULAW",
        "ALAW": "ALAW",
    }

    fake_google = ModuleType("google")
    fake_cloud = ModuleType("google.cloud")
    fake_cloud.texttospeech = fake_tts
    fake_google.cloud = fake_cloud

    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.cloud", fake_cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.texttospeech", fake_tts)

    adapter = GoogleCloudTTSAdapter(
        language_code="ru-RU",
        voice_name="ru-RU-Wavenet-C",
        voice_gender="FEMALE",
        audio_encoding="OGG_OPUS",
        timeout_seconds=7.5,
    )

    first = await adapter.synthesize("привет")
    second = await adapter.synthesize("мир")

    assert first == b"opus-bytes"
    assert second == b"opus-bytes"
    assert call_log["client_inits"] == 1
    assert call_log["timeouts"] == [7.5, 7.5]


def test_tts_settings_strict_values() -> None:
    settings = TTSSettings(
        provider="google_cloud",
        language_code="ru-RU",
        voice_name="ru-RU-Wavenet-C",
        voice_gender="FEMALE",
        audio_encoding="OGG_OPUS",
        timeout_seconds=10.0,
    )

    assert settings.provider == "google_cloud"
