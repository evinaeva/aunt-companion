"""Repository for daily_summaries table."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import aiosqlite


@dataclass(slots=True)
class DailySummary:
    user_id: int
    summary_date: date
    summary_text: str
    source_message_range_start: int | None
    source_message_range_end: int | None


class DailySummariesRepository:
    """Explicit SQL operations for daily summaries."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn

    async def upsert_or_create_for_date(
        self,
        user_id: int,
        summary_date: date,
        summary_text: str,
        source_message_range_start: int | None = None,
        source_message_range_end: int | None = None,
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO daily_summaries (
                user_id,
                summary_date,
                summary_text,
                source_message_range_start,
                source_message_range_end,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, summary_date) DO UPDATE SET
              summary_text = excluded.summary_text,
              source_message_range_start = excluded.source_message_range_start,
              source_message_range_end = excluded.source_message_range_end,
              updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                summary_date.isoformat(),
                summary_text,
                source_message_range_start,
                source_message_range_end,
            ),
        )
        await self.conn.commit()

    async def get_by_user_and_date(self, user_id: int, summary_date: date) -> DailySummary | None:
        cursor = await self.conn.execute(
            """
            SELECT user_id, summary_date, summary_text, source_message_range_start, source_message_range_end
            FROM daily_summaries
            WHERE user_id = ? AND summary_date = ?
            """,
            (user_id, summary_date.isoformat()),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return DailySummary(
            user_id=row["user_id"],
            summary_date=date.fromisoformat(row["summary_date"]),
            summary_text=row["summary_text"],
            source_message_range_start=row["source_message_range_start"],
            source_message_range_end=row["source_message_range_end"],
        )

    async def get_latest_for_user(self, user_id: int) -> DailySummary | None:
        cursor = await self.conn.execute(
            """
            SELECT user_id, summary_date, summary_text, source_message_range_start, source_message_range_end
            FROM daily_summaries
            WHERE user_id = ?
            ORDER BY summary_date DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return DailySummary(
            user_id=row["user_id"],
            summary_date=date.fromisoformat(row["summary_date"]),
            summary_text=row["summary_text"],
            source_message_range_start=row["source_message_range_start"],
            source_message_range_end=row["source_message_range_end"],
        )
