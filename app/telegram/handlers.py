"""Telegram text handlers for Phase 3 MVP."""

from __future__ import annotations

import logging

import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db import ConversationsRepository, MessagesRepository, UsersRepository
from app.domain.prompt_builder import build_chat_messages, load_system_prompt_ru
from app.llm.base import ChatClient

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer("Привет! Я Гоша. Пиши текстом. Если захочешь начать заново — /reset.")


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer("Доступные команды: /start, /help и /reset. Просто отправьте текстовое сообщение.")


@router.message(Command("reset"))
async def reset_handler(message: Message, db_conn: aiosqlite.Connection) -> None:
    from_user = message.from_user
    if from_user is None:
        await message.answer("Не удалось определить пользователя Telegram.")
        return

    users_repo = UsersRepository(db_conn)
    messages_repo = MessagesRepository(db_conn)

    try:
        user = await users_repo.get_or_create_user(
            telegram_user_id=from_user.id,
            display_name=from_user.full_name,
            is_admin=False,
        )
        await messages_repo.delete_by_user(user.id)
        await message.answer("Ок, давай с чистого листа.")
    except Exception:
        logger.exception("Reset handler failed")
        await message.answer("Не получилось сбросить историю. Попробуй ещё раз.")


@router.message(F.text)
async def text_message_handler(
    message: Message,
    db_conn: aiosqlite.Connection,
    llm_client: ChatClient,
    system_prompt: str | None = None,
    recent_context_messages: int = 4,
) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Пожалуйста, отправьте текстовое сообщение.")
        return

    from_user = message.from_user
    if from_user is None:
        await message.answer("Не удалось определить пользователя Telegram.")
        return

    users_repo = UsersRepository(db_conn)
    conversations_repo = ConversationsRepository(db_conn)
    messages_repo = MessagesRepository(db_conn)

    try:
        user = await users_repo.get_or_create_user(
            telegram_user_id=from_user.id,
            display_name=from_user.full_name,
            is_admin=False,
        )

        conversation = await conversations_repo.get_latest_for_user(user.id)
        if conversation is None:
            conversation = await conversations_repo.create_conversation(user.id, title="Основной чат")

        incoming_message = await messages_repo.add_message(
            user_id=user.id,
            conversation_id=conversation.id,
            direction="incoming",
            input_type="text",
            text=text,
            telegram_message_id=message.message_id,
        )

        recent_messages = await messages_repo.list_recent_by_user(user.id, limit=recent_context_messages)
        recent_without_current = [item for item in recent_messages if item.id != incoming_message.id]

        llm_messages = build_chat_messages(
            system_prompt=(system_prompt or load_system_prompt_ru()),
            target_user_id=user.id,
            recent_messages=recent_without_current,
            current_user_text=text,
        )

        save_assistant_reply = True
        try:
            reply_text = await llm_client.generate_reply(llm_messages)
            if not reply_text:
                reply_text = "Что-то не ответилось. Попробуй ещё раз."
                save_assistant_reply = False
        except Exception:
            logger.exception("LLM request failed")
            reply_text = "Сейчас не получается ответить. Напиши ещё раз чуть позже."
            save_assistant_reply = False

        if save_assistant_reply:
            await messages_repo.add_message(
                user_id=user.id,
                conversation_id=conversation.id,
                direction="outgoing",
                input_type="text",
                text=reply_text,
                telegram_message_id=None,
            )
        await message.answer(reply_text)
    except Exception:
        logger.exception("Text handler failed")
        await message.answer("Произошла ошибка. Попробуйте ещё раз.")
