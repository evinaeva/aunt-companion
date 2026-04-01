"""Runtime settings loaded from TOML and environment variables."""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LLM_LOCAL_CONFIG_PATH = PROJECT_ROOT / "config" / "llm.local.toml"


class TelegramSettings(BaseModel):
    """Telegram bot and access-control settings."""

    bot_token: str
    allowed_user_ids: list[int]
    admin_user_id: int


class LLMSettings(BaseModel):
    """Resolved primary LLM settings."""

    provider: str
    base_url: str
    model: str
    api_key: str = ""


class STTSettings(BaseModel):
    """Speech-to-text settings."""

    model_size: str
    compute_type: str


class TTSSettings(BaseModel):
    """Text-to-speech settings."""

    piper_voice_path: Path


class PathsSettings(BaseModel):
    """Filesystem paths used by the app."""

    data_dir: Path
    tmp_dir: Path
    log_dir: Path
    sqlite_path: Path


class Settings(BaseSettings):
    """Top-level application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "dev"
    log_level: str = "INFO"
    recent_context_messages: int = Field(default=4, alias="RECENT_CONTEXT_MESSAGES")

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    allowed_telegram_user_ids_raw: str = Field(alias="ALLOWED_TELEGRAM_USER_IDS")
    admin_telegram_user_id: int = Field(alias="ADMIN_TELEGRAM_USER_ID")

    llm_base_url: str = Field(alias="LLM_BASE_URL")
    llm_model: str = Field(alias="LLM_MODEL")
    llm_provider: str = Field(default="llama_cpp", alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")

    stt_model_size: str = Field(alias="STT_MODEL_SIZE")
    stt_compute_type: str = Field(alias="STT_COMPUTE_TYPE")

    piper_voice_path: Path = Field(alias="PIPER_VOICE_PATH")

    data_dir: Path = Field(alias="DATA_DIR")
    tmp_dir: Path = Field(alias="TMP_DIR")
    log_dir: Path = Field(alias="LOG_DIR")
    sqlite_path: Path = Field(alias="SQLITE_PATH")

    @field_validator("recent_context_messages")
    @classmethod
    def validate_recent_context_messages(cls, value: int) -> int:
        """Keep recent chat context in a small, predictable window."""
        if value < 2 or value > 20:
            raise ValueError("RECENT_CONTEXT_MESSAGES must be between 2 and 20")
        return value

    @field_validator("allowed_telegram_user_ids_raw")
    @classmethod
    def normalize_allowed_ids(cls, value: str) -> str:
        """Validate and normalize comma-separated Telegram user IDs."""
        tokens = [item.strip() for item in value.split(",") if item.strip()]
        if not tokens:
            raise ValueError("ALLOWED_TELEGRAM_USER_IDS must not be empty")

        parsed_ids: list[int] = []
        for token in tokens:
            try:
                parsed_ids.append(int(token))
            except ValueError as exc:
                raise ValueError(f"Invalid Telegram user id in ALLOWED_TELEGRAM_USER_IDS: {token}") from exc

        return ",".join(str(item) for item in parsed_ids)

    @property
    def allowed_telegram_user_ids(self) -> list[int]:
        """Parsed and normalized Telegram whitelist IDs."""
        return [int(item) for item in self.allowed_telegram_user_ids_raw.split(",") if item]

    @property
    def telegram(self) -> TelegramSettings:
        """Structured Telegram settings."""
        return TelegramSettings(
            bot_token=self.telegram_bot_token,
            allowed_user_ids=self.allowed_telegram_user_ids,
            admin_user_id=self.admin_telegram_user_id,
        )

    @property
    def llm(self) -> LLMSettings:
        """Structured LLM settings with local TOML preference."""
        toml_primary = _load_primary_llm_config(LLM_LOCAL_CONFIG_PATH)
        if toml_primary is not None:
            return LLMSettings(**toml_primary)

        return LLMSettings(
            provider=self.llm_provider,
            base_url=self.llm_base_url,
            model=self.llm_model,
            api_key=self.llm_api_key,
        )

    @property
    def stt(self) -> STTSettings:
        """Structured STT settings."""
        return STTSettings(model_size=self.stt_model_size, compute_type=self.stt_compute_type)

    @property
    def tts(self) -> TTSSettings:
        """Structured TTS settings."""
        return TTSSettings(piper_voice_path=self.piper_voice_path)

    @property
    def paths(self) -> PathsSettings:
        """Structured path settings."""
        return PathsSettings(
            data_dir=self.data_dir,
            tmp_dir=self.tmp_dir,
            log_dir=self.log_dir,
            sqlite_path=self.sqlite_path,
        )


def _load_primary_llm_config(path: Path) -> dict[str, str] | None:
    if not path.exists():
        return None

    with path.open("rb") as f:
        body = tomllib.load(f)

    primary = body.get("primary")
    if not isinstance(primary, dict):
        raise ValueError("config/llm.local.toml must contain [primary] section")

    required = ("provider", "model", "base_url", "api_key")
    resolved: dict[str, str] = {}
    for key in required:
        value = primary.get(key, "")
        if not isinstance(value, str):
            raise ValueError(f"Invalid [primary].{key} value in config/llm.local.toml")
        resolved[key] = value.strip()

    if resolved["provider"] == "gemini" and resolved["api_key"] in {"", "YOUR_GEMINI_API_KEY"}:
        raise ValueError(
            "config/llm.local.toml [primary].api_key must be set to a real Gemini API key "
            "or remove config/llm.local.toml to use .env fallback"
        )

    return resolved


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
