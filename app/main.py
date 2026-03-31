"""Application entrypoint for the Telegram text-chat MVP."""

from __future__ import annotations

import asyncio
import logging

from app.config import configure_logging, get_settings
from app.db import connect, initialize_database
from app.telegram.bot import run_polling

logger = logging.getLogger(__name__)


async def _run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Starting Gosha bot", extra={"environment": settings.environment, "db_path": str(settings.paths.sqlite_path)})

    await initialize_database(
        db_path=settings.paths.sqlite_path,
        data_dir=settings.paths.data_dir,
        tmp_dir=settings.paths.tmp_dir,
        log_dir=settings.paths.log_dir,
    )
    logger.info("Runtime directories and database initialized")

    conn = await connect(settings.paths.sqlite_path)
    logger.info("SQLite connection opened")
    try:
        await run_polling(settings, conn)
    except asyncio.CancelledError:
        logger.info("Polling task cancelled")
        raise
    except Exception:
        logger.exception("Fatal error in polling loop")
        raise
    finally:
        await conn.close()
        logger.info("SQLite connection closed")


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by keyboard interrupt")
    except Exception:
        logger.exception("Application exited with an unrecoverable error")
        raise


if __name__ == "__main__":
    main()
