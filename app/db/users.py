"""Repository for users table."""

from __future__ import annotations

from dataclasses import dataclass

import aiosqlite


@dataclass(slots=True)
class User:
    id: int
    telegram_user_id: int
    display_name: str | None
    is_admin: bool
    is_active: bool


class UsersRepository:
    """Explicit SQL operations for users."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> User | None:
        cursor = await self.conn.execute(
            """
            SELECT id, telegram_user_id, display_name, is_admin, is_active
            FROM users
            WHERE telegram_user_id = ?
            """,
            (telegram_user_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return User(
            id=row["id"],
            telegram_user_id=row["telegram_user_id"],
            display_name=row["display_name"],
            is_admin=bool(row["is_admin"]),
            is_active=bool(row["is_active"]),
        )

    async def create_user(self, telegram_user_id: int, display_name: str | None, is_admin: bool) -> User:
        cursor = await self.conn.execute(
            """
            INSERT INTO users (telegram_user_id, display_name, is_admin)
            VALUES (?, ?, ?)
            """,
            (telegram_user_id, display_name, int(is_admin)),
        )
        await self.conn.commit()
        return User(
            id=cursor.lastrowid,
            telegram_user_id=telegram_user_id,
            display_name=display_name,
            is_admin=is_admin,
            is_active=True,
        )

    async def get_or_create_user(
        self, telegram_user_id: int, display_name: str | None = None, is_admin: bool = False
    ) -> User:
        user = await self.get_by_telegram_user_id(telegram_user_id)
        if user is not None:
            return user
        return await self.create_user(telegram_user_id, display_name, is_admin)
