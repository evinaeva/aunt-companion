"""Repository for user_settings table."""

from __future__ import annotations

from dataclasses import dataclass

import aiosqlite


@dataclass(slots=True)
class UserSettings:
    user_id: int
    voice_enabled: bool
    updated_at: str


class UserSettingsRepository:
    """Explicit SQL operations for user_settings."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn

    async def get_by_user_id(self, user_id: int) -> UserSettings | None:
        cursor = await self.conn.execute(
            """
            SELECT user_id, voice_enabled, updated_at
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
            voice_enabled=bool(row["voice_enabled"]),
            updated_at=row["updated_at"],
        )

    async def get_or_create_user_settings(self, user_id: int) -> UserSettings:
        await self.conn.execute(
            """
            INSERT INTO user_settings (user_id, voice_enabled, updated_at)
            VALUES (?, 0, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO NOTHING
            """,
            (user_id,),
        )
        await self.conn.commit()
        saved = await self.get_by_user_id(user_id)
        assert saved is not None
        return saved

    async def set_voice_enabled(self, user_id: int, enabled: bool) -> None:
        await self.conn.execute(
            """
            INSERT INTO user_settings (user_id, voice_enabled, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
              voice_enabled = excluded.voice_enabled,
              updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, int(enabled)),
        )
        await self.conn.commit()

    async def is_voice_enabled(self, user_id: int) -> bool:
        saved = await self.get_or_create_user_settings(user_id)
        return saved.voice_enabled
