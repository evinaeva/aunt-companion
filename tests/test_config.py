from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings


def set_base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "000:token")
    monkeypatch.setenv("ADMIN_TELEGRAM_USER_ID", "1")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:8012")
    monkeypatch.setenv("LLM_MODEL", "Qwen3-4B-Q5_K_M")
    monkeypatch.setenv("STT_MODEL_SIZE", "small")
    monkeypatch.setenv("STT_COMPUTE_TYPE", "int8")
    monkeypatch.setenv("PIPER_VOICE_PATH", "./data/models/tts/ru_RU-irina-medium.onnx")
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
