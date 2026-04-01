from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.config import settings as settings_mod
from app.llm.client import LlamaClient
from app.llm.factory import build_primary_chat_client
from app.llm.gemini_client import GeminiClient


def set_base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "000:token")
    monkeypatch.setenv("ALLOWED_TELEGRAM_USER_IDS", "1,2")
    monkeypatch.setenv("ADMIN_TELEGRAM_USER_ID", "1")
    monkeypatch.setenv("LLM_PROVIDER", "llama_cpp")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:8012")
    monkeypatch.setenv("LLM_MODEL", "Qwen3-4B-Q5_K_M")
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("STT_MODEL_SIZE", "small")
    monkeypatch.setenv("STT_COMPUTE_TYPE", "int8")
    monkeypatch.setenv("PIPER_VOICE_PATH", "./data/models/tts/ru_RU-irina-medium.onnx")
    monkeypatch.setenv("DATA_DIR", "./data")
    monkeypatch.setenv("TMP_DIR", "./data/tmp")
    monkeypatch.setenv("LOG_DIR", "./data/logs")
    monkeypatch.setenv("SQLITE_PATH", "./data/db/gosha.sqlite3")


def test_settings_loads_primary_from_local_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    set_base_env(monkeypatch)
    cfg_path = tmp_path / "llm.local.toml"
    cfg_path.write_text(
        """
[primary]
provider = "gemini"
model = "gemini-2.5-flash-lite"
base_url = "https://generativelanguage.googleapis.com"
api_key = "test-key"
""".strip()
    )

    monkeypatch.setattr(settings_mod, "LLM_LOCAL_CONFIG_PATH", cfg_path)
    settings = Settings()

    assert settings.llm.provider == "gemini"
    assert settings.llm.model == "gemini-2.5-flash-lite"
    assert settings.llm.base_url == "https://generativelanguage.googleapis.com"
    assert settings.llm.api_key == "test-key"


def test_settings_falls_back_to_env_when_local_toml_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    set_base_env(monkeypatch)
    monkeypatch.setattr(settings_mod, "LLM_LOCAL_CONFIG_PATH", tmp_path / "missing.toml")

    settings = Settings()

    assert settings.llm.provider == "llama_cpp"
    assert settings.llm.model == "Qwen3-4B-Q5_K_M"


def test_settings_rejects_placeholder_gemini_api_key_in_local_toml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    set_base_env(monkeypatch)
    cfg_path = tmp_path / "llm.local.toml"
    cfg_path.write_text(
        """
[primary]
provider = "gemini"
model = "gemini-2.5-flash-lite"
base_url = "https://generativelanguage.googleapis.com"
api_key = "YOUR_GEMINI_API_KEY"
""".strip()
    )
    monkeypatch.setattr(settings_mod, "LLM_LOCAL_CONFIG_PATH", cfg_path)

    settings = Settings()

    with pytest.raises(ValueError, match="must be set to a real Gemini API key"):
        _ = settings.llm


def test_factory_selects_primary_provider(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    set_base_env(monkeypatch)
    cfg_path = tmp_path / "llm.local.toml"
    cfg_path.write_text(
        """
[primary]
provider = "llama_cpp"
model = "gemma-3-1b-it-Q4_K_M"
base_url = "http://127.0.0.1:8012"
api_key = ""
""".strip()
    )
    monkeypatch.setattr(settings_mod, "LLM_LOCAL_CONFIG_PATH", cfg_path)

    client = build_primary_chat_client(Settings())

    assert isinstance(client, LlamaClient)


@pytest.mark.asyncio
async def test_gemini_adapter_sends_prompt_and_system_instruction(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    class FakeModels:
        def generate_content(self, *, model, contents, config):
            calls["model"] = model
            calls["contents"] = contents
            calls["config"] = config
            return type("Resp", (), {"text": "Короткий ответ"})()

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.models = FakeModels()

    monkeypatch.setattr("app.llm.gemini_client.genai.Client", FakeClient)

    client = GeminiClient(
        api_key="test-key",
        model="gemini-2.5-flash-lite",
        base_url="https://generativelanguage.googleapis.com",
    )

    text = await client.generate_reply(
        [
            {"role": "system", "content": "Отвечай по-русски и коротко."},
            {"role": "user", "content": "Привет"},
        ]
    )

    assert text == "Короткий ответ"
    assert calls["model"] == "gemini-2.5-flash-lite"
    assert "Пользователь: Привет" in str(calls["contents"])
    assert getattr(calls["config"], "system_instruction") == "Отвечай по-русски и коротко."
