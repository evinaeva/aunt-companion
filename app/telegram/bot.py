"""Telegram bot startup in polling mode for text MVP."""

from __future__ import annotations

import logging

import aiosqlite
from aiogram import Bot, Dispatcher

from app.config import Settings
from app.llm.factory import build_primary_chat_client
from app.telegram.handlers import router
from app.telegram.middleware import WhitelistMiddleware

logger = logging.getLogger(__name__)


async def run_polling(settings: Settings, db_conn: aiosqlite.Connection) -> None:
    """Start aiogram polling with minimal dependencies wired in."""
    bot = Bot(token=settings.telegram.bot_token)
    dp = Dispatcher()

    dp.message.middleware(WhitelistMiddleware(set(settings.telegram.allowed_user_ids)))
    dp.include_router(router)

    llm_client = build_primary_chat_client(settings)

    logger.info(
        "Starting Telegram polling",
        extra={
            "allowed_users_count": len(settings.telegram.allowed_user_ids),
            "llm_base_url": settings.llm.base_url,
            "llm_model": settings.llm.model,
        },
    )
    try:
        await dp.start_polling(bot, db_conn=db_conn, llm_client=llm_client)
    finally:
        await bot.session.close()
        logger.info("Telegram polling stopped and bot session closed")
