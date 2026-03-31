"""Telegram bot startup in polling mode for text MVP."""

from __future__ import annotations

import aiosqlite
from aiogram import Bot, Dispatcher

from app.config import Settings
from app.llm.client import LlamaClient
from app.telegram.handlers import router
from app.telegram.middleware import WhitelistMiddleware


async def run_polling(settings: Settings, db_conn: aiosqlite.Connection) -> None:
    """Start aiogram polling with minimal dependencies wired in."""
    bot = Bot(token=settings.telegram.bot_token)
    dp = Dispatcher()

    dp.message.middleware(WhitelistMiddleware(set(settings.telegram.allowed_user_ids)))
    dp.include_router(router)

    llm_client = LlamaClient(base_url=settings.llm.base_url, model=settings.llm.model)
    await dp.start_polling(bot, db_conn=db_conn, llm_client=llm_client)
