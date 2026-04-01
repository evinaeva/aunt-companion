"""Repository for messages table."""

from __future__ import annotations

from dataclasses import dataclass

import aiosqlite


@dataclass(slots=True)
class Message:
    id: int
    user_id: int
    conversation_id: int | None
    direction: str
    input_type: str
    text: str
    telegram_message_id: int | None


class MessagesRepository:
    """Explicit SQL operations for messages."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn

    async def add_message(
        self,
        user_id: int,
        direction: str,
        input_type: str,
        text: str,
        conversation_id: int | None = None,
        telegram_message_id: int | None = None,
    ) -> Message:
        cursor = await self.conn.execute(
            """
            INSERT INTO messages (
                user_id,
                conversation_id,
                direction,
                input_type,
                text,
                telegram_message_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, conversation_id, direction, input_type, text, telegram_message_id),
        )
        await self.conn.commit()
        return Message(
            id=cursor.lastrowid,
            user_id=user_id,
            conversation_id=conversation_id,
            direction=direction,
            input_type=input_type,
            text=text,
            telegram_message_id=telegram_message_id,
        )

    async def list_recent_by_user(self, user_id: int, limit: int = 10) -> list[Message]:
        cursor = await self.conn.execute(
            """
            SELECT id, user_id, conversation_id, direction, input_type, text, telegram_message_id
            FROM messages
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            Message(
                id=row["id"],
                user_id=row["user_id"],
                conversation_id=row["conversation_id"],
                direction=row["direction"],
                input_type=row["input_type"],
                text=row["text"],
                telegram_message_id=row["telegram_message_id"],
            )
            for row in rows
        ]

    async def delete_by_user(self, user_id: int) -> int:
        """Delete all message history for a specific user."""
        cursor = await self.conn.execute(
            """
            DELETE FROM messages
            WHERE user_id = ?
            """,
            (user_id,),
        )
        await self.conn.commit()
        return cursor.rowcount
