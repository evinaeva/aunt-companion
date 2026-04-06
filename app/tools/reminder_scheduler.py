"""Scheduler abstraction for persisted reminders."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


class ReminderScheduler(Protocol):
    async def schedule(self, *, reminder_id: int, user_id: int, run_at_utc: datetime) -> None:
        """Schedule reminder delivery in background infra."""


@dataclass(slots=True)
class InMemoryReminderScheduler:
    """Simple scheduler used by default and in tests."""

    scheduled: list[tuple[int, int, datetime]] = field(default_factory=list)

    async def schedule(self, *, reminder_id: int, user_id: int, run_at_utc: datetime) -> None:
        self.scheduled.append((reminder_id, user_id, run_at_utc))
