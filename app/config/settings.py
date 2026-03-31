"""Runtime settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramSettings(BaseModel):
    """Telegram bot and access-control settings."""

    bot_token: str
    allowed_user_ids: list[int]
    admin_user_id: int


class LLMSettings(BaseModel):
    """Local llama.cpp server settings."""

    base_url: str
    model: str


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

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    allowed_telegram_user_ids_raw: str = Field(alias="ALLOWED_TELEGRAM_USER_IDS")
    admin_telegram_user_id: int = Field(alias="ADMIN_TELEGRAM_USER_ID")

    llm_base_url: str = Field(alias="LLM_BASE_URL")
    llm_model: str = Field(alias="LLM_MODEL")

    stt_model_size: str = Field(alias="STT_MODEL_SIZE")
    stt_compute_type: str = Field(alias="STT_COMPUTE_TYPE")

    piper_voice_path: Path = Field(alias="PIPER_VOICE_PATH")

    data_dir: Path = Field(alias="DATA_DIR")
    tmp_dir: Path = Field(alias="TMP_DIR")
    log_dir: Path = Field(alias="LOG_DIR")
    sqlite_path: Path = Field(alias="SQLITE_PATH")

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
        """Structured LLM settings."""
        return LLMSettings(base_url=self.llm_base_url, model=self.llm_model)

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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
