from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.db.repositories.reminders import RemindersRepository
from app.db.sqlite import connect, initialize_database


@pytest.mark.asyncio
async def test_reminders_repository_user_scoped_and_due_queries(tmp_path: Path) -> None:
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
        await conn.execute("INSERT INTO users (id, telegram_user_id, display_name, is_admin, is_active) VALUES (2, 1002, 'B', 0, 1)")
        await conn.commit()

        repo = RemindersRepository(conn)
        now = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
        await repo.create_reminder(
            user_id=1,
            title="A-reminder",
            remind_at_utc=now + timedelta(minutes=10),
            timezone="UTC",
        )
        reminder_b = await repo.create_reminder(
            user_id=2,
            title="B-reminder",
            remind_at_utc=now - timedelta(minutes=10),
            timezone="UTC",
        )

        by_user = await repo.list_by_user(1)
        due = await repo.list_due(now_utc=now)
        await repo.mark_dispatched(reminder_b.id)
        due_after_dispatch = await repo.list_due(now_utc=now)
    finally:
        await conn.close()

    assert len(by_user) == 1
    assert by_user[0].title == "A-reminder"
    assert len(due) == 1
    assert due[0].user_id == 2
    assert due_after_dispatch == []
