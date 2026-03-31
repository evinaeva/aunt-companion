"""Repository for profile_facts table."""

from __future__ import annotations

from dataclasses import dataclass

import aiosqlite


@dataclass(slots=True)
class ProfileFact:
    user_id: int
    fact_key: str
    fact_value: str
    confidence: float
    source_message_id: int | None


class ProfileFactsRepository:
    """Explicit SQL operations for profile_facts."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn

    async def upsert_fact(
        self,
        user_id: int,
        fact_key: str,
        fact_value: str,
        confidence: float,
        source_message_id: int | None = None,
    ) -> None:
        await self.conn.execute(
            """
            INSERT INTO profile_facts (
                user_id,
                fact_key,
                fact_value,
                confidence,
                source_message_id,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, fact_key) DO UPDATE SET
              fact_value = excluded.fact_value,
              confidence = excluded.confidence,
              source_message_id = excluded.source_message_id,
              updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, fact_key, fact_value, confidence, source_message_id),
        )
        await self.conn.commit()

    async def list_by_user(self, user_id: int) -> list[ProfileFact]:
        cursor = await self.conn.execute(
            """
            SELECT user_id, fact_key, fact_value, confidence, source_message_id
            FROM profile_facts
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [
            ProfileFact(
                user_id=row["user_id"],
                fact_key=row["fact_key"],
                fact_value=row["fact_value"],
                confidence=row["confidence"],
                source_message_id=row["source_message_id"],
            )
            for row in rows
        ]
