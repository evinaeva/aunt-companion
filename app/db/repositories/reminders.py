"""Repository for persisted reminders."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import aiosqlite


@dataclass(slots=True, frozen=True)
class ReminderRecord:
    id: int
    user_id: int
    title: str
    remind_at_utc: datetime
    timezone: str
    status: str
    created_at: datetime


class RemindersRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn

    async def create_reminder(self, *, user_id: int, title: str, remind_at_utc: datetime, timezone: str) -> ReminderRecord:
        cursor = await self.conn.execute(
            """
            INSERT INTO reminders (user_id, title, remind_at_utc, timezone, status)
            VALUES (?, ?, ?, ?, 'scheduled')
            """,
            (user_id, title, remind_at_utc.isoformat(), timezone),
        )
        await self.conn.commit()

        reminder_id = int(cursor.lastrowid)
        row = await self._get_by_id(reminder_id)
        assert row is not None
        return row

    async def list_by_user(self, user_id: int, *, limit: int = 20) -> list[ReminderRecord]:
        cursor = await self.conn.execute(
            """
            SELECT id, user_id, title, remind_at_utc, timezone, status, created_at
            FROM reminders
            WHERE user_id = ?
            ORDER BY remind_at_utc ASC, id ASC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [self._row_to_record(row) for row in rows]

    async def list_due(self, *, now_utc: datetime, limit: int = 50) -> list[ReminderRecord]:
        cursor = await self.conn.execute(
            """
            SELECT id, user_id, title, remind_at_utc, timezone, status, created_at
            FROM reminders
            WHERE status = 'scheduled' AND remind_at_utc <= ?
            ORDER BY remind_at_utc ASC, id ASC
            LIMIT ?
            """,
            (now_utc.isoformat(), limit),
        )
        rows = await cursor.fetchall()
        return [self._row_to_record(row) for row in rows]

    async def mark_dispatched(self, reminder_id: int) -> None:
        await self.conn.execute("UPDATE reminders SET status = 'sent' WHERE id = ?", (reminder_id,))
        await self.conn.commit()

    async def _get_by_id(self, reminder_id: int) -> ReminderRecord | None:
        cursor = await self.conn.execute(
            """
            SELECT id, user_id, title, remind_at_utc, timezone, status, created_at
            FROM reminders
            WHERE id = ?
            """,
            (reminder_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def _row_to_record(self, row: aiosqlite.Row) -> ReminderRecord:
        return ReminderRecord(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            remind_at_utc=datetime.fromisoformat(row["remind_at_utc"]),
            timezone=row["timezone"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
