"""Repository for user_settings table."""

from __future__ import annotations

from dataclasses import dataclass

import aiosqlite


@dataclass(slots=True)
class UserSettings:
    user_id: int
    reply_mode: str
    voice_enabled: bool
    tts_voice: str
    language_code: str


class UserSettingsRepository:
    """Explicit SQL operations for user_settings."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn

    async def get_by_user_id(self, user_id: int) -> UserSettings | None:
        cursor = await self.conn.execute(
            """
            SELECT user_id, reply_mode, voice_enabled, tts_voice, language_code
            FROM user_settings
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return UserSettings(
            user_id=row["user_id"],
            reply_mode=row["reply_mode"],
            voice_enabled=bool(row["voice_enabled"]),
            tts_voice=row["tts_voice"],
            language_code=row["language_code"],
        )

    async def upsert_settings(
        self,
        user_id: int,
        reply_mode: str,
        tts_voice: str,
        language_code: str,
        voice_enabled: bool | None = None,
    ) -> None:
        resolved_voice_enabled = int(voice_enabled) if voice_enabled is not None else int(reply_mode == "voice")
        await self.conn.execute(
            """
            INSERT INTO user_settings (user_id, reply_mode, voice_enabled, tts_voice, language_code, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
              reply_mode = excluded.reply_mode,
              voice_enabled = excluded.voice_enabled,
              tts_voice = excluded.tts_voice,
              language_code = excluded.language_code,
              updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, reply_mode, resolved_voice_enabled, tts_voice, language_code),
        )
        await self.conn.commit()

    async def set_voice_enabled(self, user_id: int, enabled: bool, *, default_tts_voice: str, language_code: str = "ru") -> None:
        await self.upsert_settings(
            user_id=user_id,
            reply_mode="voice" if enabled else "text",
            voice_enabled=enabled,
            tts_voice=default_tts_voice,
            language_code=language_code,
        )
