"""Telegram middleware for whitelist access control."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message


class WhitelistMiddleware(BaseMiddleware):
    """Reject non-whitelisted users with a polite Russian response."""

    def __init__(self, allowed_user_ids: set[int]) -> None:
        self.allowed_user_ids = allowed_user_ids

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        from_user = event.from_user
        if from_user is None or from_user.id not in self.allowed_user_ids:
            await event.answer("Извините, доступ к этому боту ограничен.")
            return None

        return await handler(event, data)
