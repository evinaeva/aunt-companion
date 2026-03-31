"""Repository for conversations table."""

from __future__ import annotations

from dataclasses import dataclass

import aiosqlite


@dataclass(slots=True)
class Conversation:
    id: int
    user_id: int
    title: str | None


class ConversationsRepository:
    """Explicit SQL operations for conversations."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn

    async def create_conversation(self, user_id: int, title: str | None = None) -> Conversation:
        cursor = await self.conn.execute(
            """
            INSERT INTO conversations (user_id, title)
            VALUES (?, ?)
            """,
            (user_id, title),
        )
        await self.conn.commit()
        return Conversation(id=cursor.lastrowid, user_id=user_id, title=title)

    async def get_latest_for_user(self, user_id: int) -> Conversation | None:
        cursor = await self.conn.execute(
            """
            SELECT id, user_id, title
            FROM conversations
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return Conversation(id=row["id"], user_id=row["user_id"], title=row["title"])
