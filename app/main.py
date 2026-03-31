"""Application entrypoint for Phase 3 text-chat MVP."""

from __future__ import annotations

import asyncio

from app.config import configure_logging, get_settings
from app.db import connect, initialize_database
from app.telegram.bot import run_polling


async def _run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    await initialize_database(
        db_path=settings.paths.sqlite_path,
        data_dir=settings.paths.data_dir,
        tmp_dir=settings.paths.tmp_dir,
        log_dir=settings.paths.log_dir,
    )

    conn = await connect(settings.paths.sqlite_path)
    try:
        await run_polling(settings, conn)
    finally:
        await conn.close()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
