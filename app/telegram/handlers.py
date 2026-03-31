"""Telegram text handlers for Phase 3 MVP."""

from __future__ import annotations

import logging

import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.db import ConversationsRepository, MessagesRepository, UsersRepository
from app.domain.prompt_builder import build_chat_messages, load_system_prompt_ru
from app.llm.client import LlamaClient

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer("Привет! Я Гоша. Пиши текстом, и я постараюсь помочь коротко и по делу.")


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer("Доступные команды: /start и /help. Просто отправьте текстовое сообщение.")


@router.message(F.text)
async def text_message_handler(message: Message, db_conn: aiosqlite.Connection, llm_client: LlamaClient) -> None:
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

        recent_messages = await messages_repo.list_recent_by_user(user.id, limit=10)
        recent_without_current = [item for item in recent_messages if item.id != incoming_message.id]

        llm_messages = build_chat_messages(
            system_prompt=load_system_prompt_ru(),
            target_user_id=user.id,
            recent_messages=recent_without_current,
            current_user_text=text,
        )

        try:
            reply_text = await llm_client.generate_reply(llm_messages)
            if not reply_text:
                reply_text = "Извините, не получилось сформировать ответ. Попробуйте ещё раз."
        except Exception:
            logger.exception("LLM request failed")
            reply_text = "Сейчас не могу ответить. Попробуйте ещё раз чуть позже."

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
