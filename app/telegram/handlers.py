"""Telegram text handlers for Phase 3 MVP."""

from __future__ import annotations

import logging
import asyncio
import shutil
import tempfile
from pathlib import Path

import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from aiogram.types import Message

from app.db import ConversationsRepository, MessagesRepository, UserSettingsRepository, UsersRepository
from app.domain.prompt_builder import build_chat_messages, load_system_prompt_ru
from app.llm.base import ChatClient
from app.stt.engine import STTAdapter
from app.tts.engine import TTSAdapter

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! Я Гоша. Можно писать текстом или отправлять голосовые — пойму и отвечу. "
        "Начать заново — /reset. Голосовые ответы: /voice_on / /voice_off."
    )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "Доступные команды: /start, /help, /reset, /voice_on, /voice_off. "
        "Можно отправлять текст и voice-сообщения."
    )


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


@router.message(Command("voice_on"))
async def voice_on_handler(message: Message, db_conn: aiosqlite.Connection) -> None:
    await _set_voice_toggle(message, db_conn, enabled=True)


@router.message(Command("voice_off"))
async def voice_off_handler(message: Message, db_conn: aiosqlite.Connection) -> None:
    await _set_voice_toggle(message, db_conn, enabled=False)


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

    try:
        reply_text, _, _ = await _generate_and_persist_reply(
            db_conn=db_conn,
            llm_client=llm_client,
            telegram_user_id=from_user.id,
            full_name=from_user.full_name,
            incoming_text=text,
            telegram_message_id=message.message_id,
            input_type="text",
            system_prompt=system_prompt,
            recent_context_messages=recent_context_messages,
        )
        await message.answer(reply_text)
    except Exception:
        logger.exception("Text handler failed")
        await message.answer("Произошла ошибка. Попробуйте ещё раз.")


@router.message(F.voice)
async def voice_message_handler(
    message: Message,
    db_conn: aiosqlite.Connection,
    llm_client: ChatClient,
    stt_adapter: STTAdapter,
    tts_adapter: TTSAdapter,
    tmp_dir: Path,
    system_prompt: str | None = None,
    recent_context_messages: int = 4,
) -> None:
    from_user = message.from_user
    if from_user is None or message.voice is None:
        await message.answer("Не удалось определить голосовое сообщение.")
        return
    if shutil.which("ffmpeg") is None:
        await message.answer("Голосовой режим недоступен: ffmpeg не найден.")
        return

    try:
        logger.info("Voice received", extra={"telegram_user_id": from_user.id, "telegram_message_id": message.message_id})
        with tempfile.TemporaryDirectory(dir=tmp_dir) as workdir:
            src_path = Path(workdir) / "input.ogg"
            wav_path = Path(workdir) / "input.wav"
            tg_file = await message.bot.get_file(message.voice.file_id)
            await message.bot.download_file(tg_file.file_path, destination=src_path)
            logger.info("voice file downloaded", extra={"telegram_user_id": from_user.id})

            proc = await asyncio.create_subprocess_exec(
                "ffmpeg",
                "-y",
                "-i",
                str(src_path),
                "-ar",
                "16000",
                "-ac",
                "1",
                str(wav_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, ffmpeg_err = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"ffmpeg convert failed: {ffmpeg_err.decode('utf-8', errors='ignore')}")
            logger.info("audio converted", extra={"telegram_user_id": from_user.id})

            try:
                transcript = await stt_adapter.transcribe(str(wav_path))
                logger.info("transcript ready", extra={"telegram_user_id": from_user.id, "transcript_len": len(transcript)})
            except Exception:
                logger.exception("STT request failed")
                logger.info("fallback path triggered", extra={"telegram_user_id": from_user.id, "stage": "stt_failed"})
                await message.answer("Не разобрал голос. Попробуй ещё раз.")
                return
            if not transcript.strip():
                logger.info("fallback path triggered", extra={"telegram_user_id": from_user.id, "stage": "empty_transcript"})
                await message.answer("Не разобрал голос. Попробуй ещё раз.")
                return

        reply_text, should_store, user_id = await _generate_and_persist_reply(
            db_conn=db_conn,
            llm_client=llm_client,
            telegram_user_id=from_user.id,
            full_name=from_user.full_name,
            incoming_text=transcript,
            telegram_message_id=message.message_id,
            input_type="voice",
            system_prompt=system_prompt,
            recent_context_messages=recent_context_messages,
        )

        settings_repo = UserSettingsRepository(db_conn)
        should_voice_reply = await settings_repo.is_voice_enabled(user_id)
        if should_voice_reply:
            try:
                voice_data = await tts_adapter.synthesize(reply_text)
                await message.answer_voice(BufferedInputFile(voice_data, filename="reply.ogg"))
                logger.info("tts synthesized", extra={"telegram_user_id": from_user.id})
                logger.info("voice sent", extra={"telegram_user_id": from_user.id})
            except Exception:
                logger.exception("TTS request failed")
                logger.info("fallback path triggered", extra={"telegram_user_id": from_user.id, "stage": "tts_failed"})
                await message.answer(reply_text)
            return

        logger.info("Fallback to text by user setting voice_off", extra={"telegram_user_id": from_user.id})
        await message.answer(reply_text)
    except Exception:
        logger.exception("Voice handler failed")
        await message.answer("Произошла ошибка. Попробуйте ещё раз.")


async def _set_voice_toggle(message: Message, db_conn: aiosqlite.Connection, *, enabled: bool) -> None:
    from_user = message.from_user
    if from_user is None:
        await message.answer("Не удалось определить пользователя Telegram.")
        return
    users_repo = UsersRepository(db_conn)
    settings_repo = UserSettingsRepository(db_conn)
    user = await users_repo.get_or_create_user(telegram_user_id=from_user.id, display_name=from_user.full_name, is_admin=False)
    await settings_repo.set_voice_enabled(user.id, enabled=enabled)
    await message.answer("Голосовые ответы включены." if enabled else "Голосовые ответы выключены.")


async def _generate_and_persist_reply(
    *,
    db_conn: aiosqlite.Connection,
    llm_client: ChatClient,
    telegram_user_id: int,
    full_name: str,
    incoming_text: str,
    telegram_message_id: int | None,
    input_type: str,
    system_prompt: str | None,
    recent_context_messages: int,
) -> tuple[str, bool, int]:
    users_repo = UsersRepository(db_conn)
    conversations_repo = ConversationsRepository(db_conn)
    messages_repo = MessagesRepository(db_conn)
    user = await users_repo.get_or_create_user(telegram_user_id=telegram_user_id, display_name=full_name, is_admin=False)
    conversation = await conversations_repo.get_latest_for_user(user.id)
    if conversation is None:
        conversation = await conversations_repo.create_conversation(user.id, title="Основной чат")
    incoming_message = await messages_repo.add_message(
        user_id=user.id,
        conversation_id=conversation.id,
        direction="incoming",
        input_type=input_type,
        text=incoming_text,
        telegram_message_id=telegram_message_id,
    )
    recent_messages = await messages_repo.list_recent_by_user(user.id, limit=recent_context_messages)
    recent_without_current = [item for item in recent_messages if item.id != incoming_message.id]
    llm_messages = build_chat_messages(
        system_prompt=(system_prompt or load_system_prompt_ru()),
        target_user_id=user.id,
        recent_messages=recent_without_current,
        current_user_text=incoming_text,
    )
    save_assistant_reply = True
    try:
        llm_response = await llm_client.generate(llm_messages)
        reply_text = llm_response.text.strip()
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
    return reply_text, save_assistant_reply, user.id
