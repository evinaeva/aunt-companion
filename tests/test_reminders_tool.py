from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

import pytest

from app.db.repositories.reminders import RemindersRepository
from app.db.sqlite import connect, initialize_database
from app.llm.tool_context import ToolRequestContext
from app.tools.reminder_scheduler import InMemoryReminderScheduler
from app.tools.reminder_service import ReminderService
from app.tools.reminders_tool import build_reminders_tool


@pytest.mark.asyncio
async def test_reminders_tool_validates_and_persists_with_timezone(tmp_path: Path) -> None:
    db_path = tmp_path / "runtime" / "data" / "db" / "gosha.sqlite3"
    await initialize_database(
        db_path,
        data_dir=tmp_path / "runtime" / "data",
        tmp_dir=tmp_path / "runtime" / "tmp",
        log_dir=tmp_path / "runtime" / "logs",
    )

    conn = await connect(db_path)
    try:
        await conn.execute("INSERT INTO users (id, telegram_user_id, display_name, is_admin, is_active) VALUES (1, 1001, 'A', 0, 1)")
        await conn.commit()

        scheduler = InMemoryReminderScheduler()
        service = ReminderService(reminders_repository=RemindersRepository(conn), scheduler=scheduler)
        tool = build_reminders_tool(service=service)

        berlin_now = datetime.now(ZoneInfo("Europe/Berlin"))
        local_time = (berlin_now + timedelta(hours=2)).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")
        context = ToolRequestContext(
            user_id=1,
            telegram_user_id=1001,
            now_utc=datetime.now(UTC),
            timezone="Europe/Berlin",
        )

        result = await tool.handler(context, {"title": "  Buy milk  ", "remind_at": local_time})
        reminders = await RemindersRepository(conn).list_by_user(1)
    finally:
        await conn.close()

    assert result["status"] == "scheduled"
    assert reminders[0].title == "Buy milk"
    assert reminders[0].timezone == "Europe/Berlin"
    assert len(scheduler.scheduled) == 1


@pytest.mark.asyncio
async def test_reminders_tool_rejects_invalid_payload(tmp_path: Path) -> None:
    db_path = tmp_path / "runtime" / "data" / "db" / "gosha.sqlite3"
    await initialize_database(
        db_path,
        data_dir=tmp_path / "runtime" / "data",
        tmp_dir=tmp_path / "runtime" / "tmp",
        log_dir=tmp_path / "runtime" / "logs",
    )
    conn = await connect(db_path)
    try:
        await conn.execute("INSERT INTO users (id, telegram_user_id, display_name, is_admin, is_active) VALUES (1, 1001, 'A', 0, 1)")
        await conn.commit()
        service = ReminderService(reminders_repository=RemindersRepository(conn), scheduler=InMemoryReminderScheduler())
        tool = build_reminders_tool(service=service)
        context = ToolRequestContext(
            user_id=1,
            telegram_user_id=1001,
            now_utc=datetime.now(UTC),
            timezone="Europe/Berlin",
        )

        with pytest.raises(ValueError, match="Reminder title"):
            await tool.handler(context, {"title": "   ", "remind_at": "2026-04-01T12:00:00"})
    finally:
        await conn.close()
