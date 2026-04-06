"""SQLite connection and schema initialization for Gosha."""

from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

from app.db.directories import ensure_runtime_directories

BUSY_TIMEOUT_MS = 5000
logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id INTEGER NOT NULL UNIQUE,
    display_name TEXT,
    is_admin INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    voice_enabled INTEGER NOT NULL DEFAULT 0 CHECK (voice_enabled IN (0, 1)),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    conversation_id INTEGER,
    direction TEXT NOT NULL CHECK (direction IN ('incoming', 'outgoing')),
    input_type TEXT NOT NULL CHECK (input_type IN ('text', 'voice', 'command')),
    text TEXT NOT NULL,
    telegram_message_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_user_created_at
ON messages(user_id, created_at DESC, id DESC);

CREATE TABLE IF NOT EXISTS profile_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fact_key TEXT NOT NULL,
    fact_value TEXT NOT NULL,
    confidence REAL NOT NULL,
    source_message_id INTEGER,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (source_message_id) REFERENCES messages(id) ON DELETE SET NULL,
    UNIQUE (user_id, fact_key)
);

CREATE TABLE IF NOT EXISTS daily_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    summary_date TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    source_message_range_start INTEGER,
    source_message_range_end INTEGER,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user_id, summary_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_summaries_user_date
ON daily_summaries(user_id, summary_date DESC);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    remind_at_utc TEXT NOT NULL,
    timezone TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'sent', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reminders_user_time
ON reminders(user_id, remind_at_utc ASC, id ASC);

CREATE INDEX IF NOT EXISTS idx_reminders_due
ON reminders(status, remind_at_utc ASC, id ASC);
"""

USER_SETTINGS_TARGET_COLUMNS = {"user_id", "voice_enabled", "updated_at"}


async def connect(db_path: Path) -> aiosqlite.Connection:
    """Open SQLite connection with required pragmas."""
    conn = await aiosqlite.connect(db_path)
    await conn.execute("PRAGMA foreign_keys = ON;")
    await conn.execute("PRAGMA journal_mode = WAL;")
    await conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS};")
    conn.row_factory = aiosqlite.Row
    return conn


async def initialize_database(
    db_path: Path,
    *,
    data_dir: Path,
    tmp_dir: Path,
    log_dir: Path,
) -> None:
    """Initialize SQLite schema and runtime directories."""
    ensure_runtime_directories(data_dir, db_path.parent, tmp_dir, log_dir)
    conn = await connect(db_path)
    try:
        await conn.executescript(SCHEMA_SQL)
        await _migrate_user_settings_schema(conn)
        await conn.commit()
    finally:
        await conn.close()


async def _migrate_user_settings_schema(conn: aiosqlite.Connection) -> None:
    cursor = await conn.execute("PRAGMA table_info(user_settings)")
    columns = [row["name"] for row in await cursor.fetchall()]
    if not columns:
        return

    if set(columns) == USER_SETTINGS_TARGET_COLUMNS:
        return

    logger.info("SQLite migration: rebuilding user_settings table", extra={"existing_columns": columns})
    has_voice_enabled = "voice_enabled" in columns
    has_reply_mode = "reply_mode" in columns
    has_updated_at = "updated_at" in columns

    voice_expr = "0"
    if has_voice_enabled and has_reply_mode:
        voice_expr = (
            "CASE "
            "WHEN voice_enabled IN (0, 1) THEN voice_enabled "
            "WHEN reply_mode = 'voice' THEN 1 "
            "ELSE 0 END"
        )
    elif has_voice_enabled:
        voice_expr = "CASE WHEN voice_enabled IN (0, 1) THEN voice_enabled ELSE 0 END"
    elif has_reply_mode:
        voice_expr = "CASE WHEN reply_mode = 'voice' THEN 1 ELSE 0 END"

    updated_expr = "updated_at" if has_updated_at else "CURRENT_TIMESTAMP"

    await conn.execute("ALTER TABLE user_settings RENAME TO user_settings_legacy")
    await conn.execute(
        """
        CREATE TABLE user_settings (
            user_id INTEGER PRIMARY KEY,
            voice_enabled INTEGER NOT NULL DEFAULT 0 CHECK (voice_enabled IN (0, 1)),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    await conn.execute(
        f"""
        INSERT INTO user_settings (user_id, voice_enabled, updated_at)
        SELECT user_id, {voice_expr}, COALESCE({updated_expr}, CURRENT_TIMESTAMP)
        FROM user_settings_legacy
        """
    )
    await conn.execute("DROP TABLE user_settings_legacy")
    logger.info("SQLite migration: user_settings table rebuilt")
