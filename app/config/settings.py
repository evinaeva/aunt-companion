"""Runtime settings loaded from TOML and environment variables."""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path

from typing import Literal

from pydantic import AliasChoices, BaseModel, Field, field_validator
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

    provider: str = "faster_whisper"
    model: str
    compute_type: str
    language: str = "ru"


class TTSSettings(BaseModel):
    """Text-to-speech settings."""

    provider: Literal["google_cloud"] = "google_cloud"
    language_code: str = "ru-RU"
    voice_name: str = ""
    voice_gender: Literal["SSML_VOICE_GENDER_UNSPECIFIED", "MALE", "FEMALE", "NEUTRAL"] = "FEMALE"
    audio_encoding: Literal["LINEAR16", "MP3", "OGG_OPUS", "MULAW", "ALAW"] = "OGG_OPUS"
    timeout_seconds: float = 10.0


class VoiceSettings(BaseModel):
    """Voice runtime feature toggles."""

    stt_provider: str = "faster_whisper"
    tts_provider: str = "google_cloud"
    voice_enabled_default: bool = False


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

    stt_model: str = Field(validation_alias=AliasChoices("STT_MODEL", "STT_MODEL_SIZE"))
    stt_compute_type: str = Field(alias="STT_COMPUTE_TYPE")
    stt_language: str = Field(default="ru", alias="STT_LANGUAGE")
    stt_provider: str = Field(default="faster_whisper", alias="STT_PROVIDER")

    tts_provider: str = Field(default="google_cloud", alias="TTS_PROVIDER")
    tts_language_code: str = Field(default="ru-RU", alias="TTS_LANGUAGE_CODE")
    tts_voice_name: str = Field(default="", alias="TTS_VOICE_NAME")
    tts_voice_gender: str = Field(default="FEMALE", alias="TTS_VOICE_GENDER")
    tts_audio_encoding: str = Field(default="OGG_OPUS", alias="TTS_AUDIO_ENCODING")
    tts_timeout_seconds: float = Field(default=10.0, alias="TTS_TIMEOUT_SECONDS")
    voice_enabled_default: bool = Field(default=False, alias="VOICE_ENABLED_DEFAULT")

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


    @field_validator("tts_provider")
    @classmethod
    def validate_tts_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized != "google_cloud":
            raise ValueError("TTS_PROVIDER must be google_cloud")
        return normalized

    @field_validator("tts_voice_gender")
    @classmethod
    def validate_tts_voice_gender(cls, value: str) -> str:
        normalized = value.strip().upper()
        allowed = {"SSML_VOICE_GENDER_UNSPECIFIED", "MALE", "FEMALE", "NEUTRAL"}
        if normalized not in allowed:
            raise ValueError("TTS_VOICE_GENDER must be one of: SSML_VOICE_GENDER_UNSPECIFIED, MALE, FEMALE, NEUTRAL")
        return normalized

    @field_validator("tts_audio_encoding")
    @classmethod
    def validate_tts_audio_encoding(cls, value: str) -> str:
        normalized = value.strip().upper()
        allowed = {"LINEAR16", "MP3", "OGG_OPUS", "MULAW", "ALAW"}
        if normalized not in allowed:
            raise ValueError("TTS_AUDIO_ENCODING must be one of: LINEAR16, MP3, OGG_OPUS, MULAW, ALAW")
        return normalized

    @field_validator("tts_timeout_seconds")
    @classmethod
    def validate_tts_timeout_seconds(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("TTS_TIMEOUT_SECONDS must be > 0")
        return value

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
        providers = _load_voice_config(LLM_LOCAL_CONFIG_PATH)
        provider = providers.get("stt_provider", self.stt_provider)
        return STTSettings(
            provider=provider,
            model=str(providers.get("stt_model", self.stt_model)),
            compute_type=str(providers.get("stt_compute_type", self.stt_compute_type)),
            language=str(providers.get("stt_language", self.stt_language)),
        )

    @property
    def tts(self) -> TTSSettings:
        """Structured TTS settings."""
        providers = _load_voice_config(LLM_LOCAL_CONFIG_PATH)
        provider = providers.get("tts_provider", self.tts_provider)
        return TTSSettings(
            provider=provider,
            language_code=str(providers.get("tts_language_code", self.tts_language_code)),
            voice_name=str(providers.get("tts_voice_name", self.tts_voice_name)),
            voice_gender=str(providers.get("tts_voice_gender", self.tts_voice_gender)).upper(),
            audio_encoding=str(providers.get("tts_audio_encoding", self.tts_audio_encoding)).upper(),
            timeout_seconds=float(providers.get("tts_timeout_seconds", self.tts_timeout_seconds)),
        )

    @property
    def voice(self) -> VoiceSettings:
        """Structured voice feature settings."""
        from_toml = _load_voice_config(LLM_LOCAL_CONFIG_PATH)
        return VoiceSettings(
            stt_provider=from_toml.get("stt_provider", self.stt_provider),
            tts_provider=from_toml.get("tts_provider", self.tts_provider),
            voice_enabled_default=from_toml.get("voice_enabled_default", self.voice_enabled_default),
        )

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


def _load_voice_config(path: Path) -> dict[str, str | bool | float]:
    if not path.exists():
        return {}

    with path.open("rb") as f:
        body = tomllib.load(f)

    voice = body.get("voice")
    if voice is None:
        return {}
    if not isinstance(voice, dict):
        raise ValueError("config/llm.local.toml [voice] must be a table")

    resolved: dict[str, str | bool | float] = {}
    for key in (
        "stt_provider",
        "tts_provider",
        "stt_model",
        "stt_compute_type",
        "stt_language",
        "tts_language_code",
        "tts_voice_name",
        "tts_voice_gender",
        "tts_audio_encoding",
    ):
        value = voice.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValueError(f"Invalid [voice].{key} value in config/llm.local.toml")
        resolved[key] = value.strip()

    if "tts_timeout_seconds" in voice:
        timeout = voice["tts_timeout_seconds"]
        if not isinstance(timeout, (int, float)):
            raise ValueError("Invalid [voice].tts_timeout_seconds value in config/llm.local.toml")
        resolved["tts_timeout_seconds"] = float(timeout)

    if "voice_enabled_default" in voice:
        enabled = voice["voice_enabled_default"]
        if not isinstance(enabled, bool):
            raise ValueError("Invalid [voice].voice_enabled_default value in config/llm.local.toml")
        resolved["voice_enabled_default"] = enabled

    return resolved


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
