from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings


def set_base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "000:token")
    monkeypatch.setenv("ADMIN_TELEGRAM_USER_ID", "1")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:8012")
    monkeypatch.setenv("LLM_MODEL", "Qwen3-4B-Q5_K_M")
    monkeypatch.setenv("STT_MODEL", "small")
    monkeypatch.setenv("STT_COMPUTE_TYPE", "int8")
    monkeypatch.setenv("STT_LANGUAGE", "ru")
    monkeypatch.setenv("TTS_PROVIDER", "google_cloud")
    monkeypatch.setenv("TTS_LANGUAGE_CODE", "ru-RU")
    monkeypatch.setenv("TTS_VOICE_NAME", "")
    monkeypatch.setenv("TTS_VOICE_GENDER", "FEMALE")
    monkeypatch.setenv("TTS_AUDIO_ENCODING", "OGG_OPUS")
    monkeypatch.setenv("DATA_DIR", "./data")
    monkeypatch.setenv("TMP_DIR", "./data/tmp")
    monkeypatch.setenv("LOG_DIR", "./data/logs")
    monkeypatch.setenv("SQLITE_PATH", "./data/db/gosha.sqlite3")


def test_settings_load_valid_comma_separated_whitelist(monkeypatch: pytest.MonkeyPatch) -> None:
    set_base_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_TELEGRAM_USER_IDS", "1,2")

    settings = Settings()

    assert settings.allowed_telegram_user_ids == [1, 2]
    assert settings.telegram.allowed_user_ids == [1, 2]
    assert settings.paths.sqlite_path == Path("./data/db/gosha.sqlite3")


def test_settings_whitelist_allows_spaces(monkeypatch: pytest.MonkeyPatch) -> None:
    set_base_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_TELEGRAM_USER_IDS", " 10, 20 , 30 ")

    settings = Settings()

    assert settings.allowed_telegram_user_ids == [10, 20, 30]


def test_settings_rejects_empty_whitelist(monkeypatch: pytest.MonkeyPatch) -> None:
    set_base_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_TELEGRAM_USER_IDS", "   ")

    with pytest.raises(ValidationError, match="ALLOWED_TELEGRAM_USER_IDS must not be empty"):
        Settings()


def test_settings_rejects_invalid_whitelist_token(monkeypatch: pytest.MonkeyPatch) -> None:
    set_base_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_TELEGRAM_USER_IDS", "1,abc")

    with pytest.raises(ValidationError, match="Invalid Telegram user id"):
        Settings()


def test_settings_recent_context_messages_default(monkeypatch: pytest.MonkeyPatch) -> None:
    set_base_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_TELEGRAM_USER_IDS", "1,2")

    settings = Settings()

    assert settings.recent_context_messages == 4


def test_settings_recent_context_messages_rejects_out_of_range(monkeypatch: pytest.MonkeyPatch) -> None:
    set_base_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_TELEGRAM_USER_IDS", "1,2")
    monkeypatch.setenv("RECENT_CONTEXT_MESSAGES", "1")

    with pytest.raises(ValidationError, match="RECENT_CONTEXT_MESSAGES must be between 2 and 20"):
        Settings()


def test_settings_rejects_invalid_tts_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    set_base_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_TELEGRAM_USER_IDS", "1,2")
    monkeypatch.setenv("TTS_PROVIDER", "piper")

    with pytest.raises(ValidationError, match="TTS_PROVIDER must be google_cloud"):
        Settings()


def test_settings_rejects_invalid_tts_audio_encoding(monkeypatch: pytest.MonkeyPatch) -> None:
    set_base_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_TELEGRAM_USER_IDS", "1,2")
    monkeypatch.setenv("TTS_AUDIO_ENCODING", "WAV")

    with pytest.raises(ValidationError, match="TTS_AUDIO_ENCODING must be one of"):
        Settings()


def test_settings_rejects_invalid_tts_voice_gender(monkeypatch: pytest.MonkeyPatch) -> None:
    set_base_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_TELEGRAM_USER_IDS", "1,2")
    monkeypatch.setenv("TTS_VOICE_GENDER", "ROBOT")

    with pytest.raises(ValidationError, match="TTS_VOICE_GENDER must be one of"):
        Settings()


def test_settings_rejects_non_positive_tts_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    set_base_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_TELEGRAM_USER_IDS", "1,2")
    monkeypatch.setenv("TTS_TIMEOUT_SECONDS", "0")

    with pytest.raises(ValidationError, match="TTS_TIMEOUT_SECONDS must be > 0"):
        Settings()
