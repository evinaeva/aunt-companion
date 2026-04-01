from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.db import (
    ConversationsRepository,
    DailySummariesRepository,
    MessagesRepository,
    ProfileFactsRepository,
    UserSettingsRepository,
    UsersRepository,
    connect,
    initialize_database,
)


@pytest.mark.asyncio
async def test_database_initialization_from_empty_path(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    data_dir = runtime_root / "custom_data"
    db_path = runtime_root / "custom_db" / "gosha.sqlite3"
    tmp_dir = runtime_root / "custom_tmp"
    log_dir = runtime_root / "custom_logs"

    await initialize_database(db_path, data_dir=data_dir, tmp_dir=tmp_dir, log_dir=log_dir)

    assert db_path.exists()
    assert data_dir.exists()
    assert db_path.parent.exists()
    assert tmp_dir.exists()
    assert log_dir.exists()


@pytest.mark.asyncio
async def test_schema_uses_daily_summaries_table_name(tmp_path: Path) -> None:
    db_path = tmp_path / "runtime" / "data" / "db" / "gosha.sqlite3"
    await initialize_database(
        db_path,
        data_dir=tmp_path / "runtime" / "data",
        tmp_dir=tmp_path / "runtime" / "data" / "tmp",
        log_dir=tmp_path / "runtime" / "data" / "logs",
    )

    conn = await connect(db_path)
    try:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('daily_summaries', 'conversation_summaries')"
        )
        rows = [row["name"] for row in await cursor.fetchall()]

    finally:
        await conn.close()

    assert "daily_summaries" in rows
    assert "conversation_summaries" not in rows


@pytest.mark.asyncio
async def test_repository_crud_basics(tmp_path: Path) -> None:
    db_path = tmp_path / "runtime" / "data" / "db" / "gosha.sqlite3"
    await initialize_database(
        db_path,
        data_dir=tmp_path / "runtime" / "data",
        tmp_dir=tmp_path / "runtime" / "data" / "tmp",
        log_dir=tmp_path / "runtime" / "data" / "logs",
    )

    conn = await connect(db_path)
    try:
        users = UsersRepository(conn)
        settings = UserSettingsRepository(conn)
        conversations = ConversationsRepository(conn)
        messages = MessagesRepository(conn)
        facts = ProfileFactsRepository(conn)
        summaries = DailySummariesRepository(conn)

        user = await users.get_or_create_user(telegram_user_id=111, display_name="Anna", is_admin=False)

        await settings.get_or_create_user_settings(user.id)
        await settings.set_voice_enabled(user.id, enabled=False)
        saved_settings = await settings.get_or_create_user_settings(user.id)

        convo = await conversations.create_conversation(user_id=user.id, title="чат")
        latest_convo = await conversations.get_latest_for_user(user.id)

        msg = await messages.add_message(
            user_id=user.id,
            direction="incoming",
            input_type="text",
            text="Привет",
            conversation_id=convo.id,
            telegram_message_id=10,
        )
        recent = await messages.list_recent_by_user(user.id, limit=5)

        await facts.upsert_fact(
            user_id=user.id,
            fact_key="name",
            fact_value="Анна",
            confidence=0.95,
            source_message_id=msg.id,
        )
        saved_facts = await facts.list_by_user(user.id)

        await summaries.upsert_or_create_for_date(
            user_id=user.id,
            summary_date=date(2026, 3, 31),
            summary_text="Короткий итог дня.",
            source_message_range_start=msg.id,
            source_message_range_end=msg.id,
        )
        latest_summary = await summaries.get_latest_for_user(user.id)
    finally:
        await conn.close()

    assert saved_settings is not None
    assert saved_settings.voice_enabled is False
    assert latest_convo is not None
    assert latest_convo.id == convo.id
    assert recent and recent[0].text == "Привет"
    assert saved_facts and saved_facts[0].fact_key == "name"
    assert latest_summary is not None
    assert latest_summary.summary_date == date(2026, 3, 31)


@pytest.mark.asyncio
async def test_strict_cross_user_isolation_queries(tmp_path: Path) -> None:
    db_path = tmp_path / "runtime" / "data" / "db" / "gosha.sqlite3"
    await initialize_database(
        db_path,
        data_dir=tmp_path / "runtime" / "data",
        tmp_dir=tmp_path / "runtime" / "data" / "tmp",
        log_dir=tmp_path / "runtime" / "data" / "logs",
    )

    conn = await connect(db_path)
    try:
        users = UsersRepository(conn)
        messages = MessagesRepository(conn)
        facts = ProfileFactsRepository(conn)
        summaries = DailySummariesRepository(conn)

        user_a = await users.get_or_create_user(telegram_user_id=1001, display_name="A", is_admin=False)
        user_b = await users.get_or_create_user(telegram_user_id=1002, display_name="B", is_admin=False)

        msg_a = await messages.add_message(user_id=user_a.id, direction="incoming", input_type="text", text="A1")
        await messages.add_message(user_id=user_b.id, direction="incoming", input_type="text", text="B1")

        await facts.upsert_fact(user_id=user_a.id, fact_key="city", fact_value="Moscow", confidence=0.9)
        await facts.upsert_fact(user_id=user_b.id, fact_key="city", fact_value="Kazan", confidence=0.9)

        await summaries.upsert_or_create_for_date(user_id=user_a.id, summary_date=date(2026, 3, 31), summary_text="A day")
        await summaries.upsert_or_create_for_date(user_id=user_b.id, summary_date=date(2026, 3, 31), summary_text="B day")

        recent_a = await messages.list_recent_by_user(user_a.id, limit=10)
        facts_a = await facts.list_by_user(user_a.id)
        summary_a = await summaries.get_by_user_and_date(user_a.id, date(2026, 3, 31))
    finally:
        await conn.close()

    assert all(item.user_id == user_a.id for item in recent_a)
    assert all(item.text != "B1" for item in recent_a)
    assert all(item.user_id == user_a.id for item in facts_a)
    assert all(item.fact_value != "Kazan" for item in facts_a)
    assert summary_a is not None
    assert summary_a.user_id == user_a.id
    assert summary_a.summary_text == "A day"
    assert msg_a.user_id == user_a.id


@pytest.mark.asyncio
async def test_user_settings_voice_toggle_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "runtime" / "data" / "db" / "gosha.sqlite3"
    await initialize_database(
        db_path,
        data_dir=tmp_path / "runtime" / "data",
        tmp_dir=tmp_path / "runtime" / "tmp",
        log_dir=tmp_path / "runtime" / "logs",
    )

    conn = await connect(db_path)
    try:
        users = UsersRepository(conn)
        settings = UserSettingsRepository(conn)
        user = await users.get_or_create_user(telegram_user_id=555, display_name="V", is_admin=False)

        assert await settings.is_voice_enabled(user.id) is False
        await settings.set_voice_enabled(user.id, enabled=True)
        assert await settings.is_voice_enabled(user.id) is True
        await settings.set_voice_enabled(user.id, enabled=False)
        assert await settings.is_voice_enabled(user.id) is False
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_initialize_database_migrates_legacy_user_settings_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "runtime" / "data" / "db" / "gosha.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = await connect(db_path)
    try:
        await conn.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL UNIQUE,
                display_name TEXT,
                is_admin INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE user_settings (
                user_id INTEGER PRIMARY KEY,
                reply_mode TEXT NOT NULL DEFAULT 'text' CHECK (reply_mode IN ('text', 'voice')),
                voice_enabled INTEGER NOT NULL DEFAULT 0 CHECK (voice_enabled IN (0, 1)),
                tts_voice TEXT NOT NULL,
                language_code TEXT NOT NULL DEFAULT 'ru',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            INSERT INTO users (id, telegram_user_id, display_name, is_admin, is_active)
            VALUES (1, 1111, 'legacy', 0, 1);
            INSERT INTO user_settings (user_id, reply_mode, voice_enabled, tts_voice, language_code, updated_at)
            VALUES (1, 'voice', 1, 'legacy-voice', 'ru', '2026-03-31 10:00:00');
            """
        )
        await conn.commit()
    finally:
        await conn.close()

    await initialize_database(
        db_path=db_path,
        data_dir=tmp_path / "runtime" / "data",
        tmp_dir=tmp_path / "runtime" / "tmp",
        log_dir=tmp_path / "runtime" / "logs",
    )

    conn = await connect(db_path)
    try:
        table_info = await conn.execute("PRAGMA table_info(user_settings)")
        columns = [row["name"] for row in await table_info.fetchall()]

        rows = await conn.execute("SELECT user_id, voice_enabled, updated_at FROM user_settings WHERE user_id = 1")
        saved = await rows.fetchone()
    finally:
        await conn.close()

    assert columns == ["user_id", "voice_enabled", "updated_at"]
    assert saved is not None
    assert saved["user_id"] == 1
    assert saved["voice_enabled"] == 1
    assert saved["updated_at"] == "2026-03-31 10:00:00"
