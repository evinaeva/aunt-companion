"""Domain service for reminder validation and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.db.repositories.reminders import ReminderRecord, RemindersRepository
from app.tools.reminder_scheduler import ReminderScheduler


@dataclass(slots=True)
class ReminderService:
    reminders_repository: RemindersRepository
    scheduler: ReminderScheduler

    async def create_reminder(self, *, user_id: int, timezone: str, title: str, remind_at_local: str) -> ReminderRecord:
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("Reminder title must not be empty")

        try:
            tz = ZoneInfo(timezone)
        except Exception as exc:
            raise ValueError(f"Unsupported timezone: {timezone}") from exc

        try:
            local_dt = datetime.fromisoformat(remind_at_local)
        except ValueError as exc:
            raise ValueError("remind_at must be ISO-8601 datetime") from exc

        if local_dt.tzinfo is None:
            local_dt = local_dt.replace(tzinfo=tz)

        remind_at_utc = local_dt.astimezone(UTC)
        if remind_at_utc <= datetime.now(UTC):
            raise ValueError("Reminder time must be in the future")

        reminder = await self.reminders_repository.create_reminder(
            user_id=user_id,
            title=normalized_title,
            remind_at_utc=remind_at_utc,
            timezone=timezone,
        )
        await self.scheduler.schedule(reminder_id=reminder.id, user_id=user_id, run_at_utc=remind_at_utc)
        return reminder
