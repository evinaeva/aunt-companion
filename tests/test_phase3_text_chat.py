from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from app.db import Message, initialize_database
from app.domain.prompt_builder import build_chat_messages, load_system_prompt_ru
from app.llm.client import LlamaClient
from app.telegram.middleware import WhitelistMiddleware


@pytest.mark.asyncio
async def test_whitelist_middleware_rejects_unknown_user() -> None:
    middleware = WhitelistMiddleware({1, 2})
    event = SimpleNamespace(from_user=SimpleNamespace(id=99), answer=AsyncMock())
    handler = AsyncMock()

    await middleware(handler, event, {})

    handler.assert_not_called()
    event.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_whitelist_middleware_allows_whitelisted_user() -> None:
    middleware = WhitelistMiddleware({1, 2})
    event = SimpleNamespace(from_user=SimpleNamespace(id=2), answer=AsyncMock())
    handler = AsyncMock(return_value="ok")

    result = await middleware(handler, event, {"x": 1})

    assert result == "ok"
    handler.assert_awaited_once()
    event.answer.assert_not_called()


def test_prompt_builder_includes_only_target_user_messages() -> None:
    recent_messages = [
        Message(
            id=1,
            user_id=101,
            conversation_id=1,
            direction="incoming",
            input_type="text",
            text="Привет",
            telegram_message_id=1,
        ),
        Message(
            id=2,
            user_id=202,
            conversation_id=2,
            direction="incoming",
            input_type="text",
            text="Чужое",
            telegram_message_id=2,
        ),
        Message(
            id=3,
            user_id=101,
            conversation_id=1,
            direction="outgoing",
            input_type="text",
            text="Здравствуйте",
            telegram_message_id=3,
        ),
    ]

    messages = build_chat_messages(
        system_prompt="system",
        target_user_id=101,
        recent_messages=recent_messages,
        current_user_text="Как дела?",
    )

    contents = [item["content"] for item in messages]
    assert "Привет" in contents
    assert "Здравствуйте" in contents
    assert "Чужое" not in contents
    assert messages[0]["role"] == "system"
    assert messages[-1] == {"role": "user", "content": "Как дела?"}


def test_prompt_builder_current_message_is_not_duplicated_when_recent_excludes_it() -> None:
    messages = build_chat_messages(
        system_prompt="system",
        target_user_id=101,
        recent_messages=[
            Message(
                id=30,
                user_id=101,
                conversation_id=1,
                direction="incoming",
                input_type="text",
                text="Старое сообщение",
                telegram_message_id=30,
            )
        ],
        current_user_text="Текущее сообщение",
    )

    user_contents = [item["content"] for item in messages if item["role"] == "user"]
    assert user_contents.count("Текущее сообщение") == 1


def test_load_system_prompt_ru_works_outside_repo_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    prompt = load_system_prompt_ru()

    assert "Ты — Гоша" in prompt


@pytest.mark.asyncio
async def test_initialize_database_accepts_keyword_db_path(tmp_path: Path) -> None:
    db_path = tmp_path / "runtime" / "db" / "gosha.sqlite3"

    await initialize_database(
        db_path=db_path,
        data_dir=tmp_path / "runtime" / "data",
        tmp_dir=tmp_path / "runtime" / "tmp",
        log_dir=tmp_path / "runtime" / "logs",
    )

    assert db_path.exists()


@pytest.mark.asyncio
async def test_main_run_uses_initialize_database_signature_consistently(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from app import main as app_main

    db_path = tmp_path / "data" / "db" / "gosha.sqlite3"
    settings = SimpleNamespace(
        environment="test",
        log_level="INFO",
        paths=SimpleNamespace(
            sqlite_path=db_path,
            data_dir=tmp_path / "data",
            tmp_dir=tmp_path / "tmp",
            log_dir=tmp_path / "logs",
        ),
    )

    captured_kwargs: dict[str, object] = {}

    async def fake_initialize_database(*args, **kwargs):
        assert not args
        captured_kwargs.update(kwargs)

    class FakeConn:
        async def close(self) -> None:
            return None

    async def fake_connect(path: Path) -> FakeConn:
        assert path == db_path
        return FakeConn()

    async def fake_run_polling(passed_settings, db_conn):
        assert passed_settings is settings
        assert isinstance(db_conn, FakeConn)

    monkeypatch.setattr(app_main, "get_settings", lambda: settings)
    monkeypatch.setattr(app_main, "configure_logging", lambda *_: None)
    monkeypatch.setattr(app_main, "initialize_database", fake_initialize_database)
    monkeypatch.setattr(app_main, "connect", fake_connect)
    monkeypatch.setattr(app_main, "run_polling", fake_run_polling)

    await app_main._run()

    assert captured_kwargs == {
        "db_path": db_path,
        "data_dir": settings.paths.data_dir,
        "tmp_dir": settings.paths.tmp_dir,
        "log_dir": settings.paths.log_dir,
    }


@pytest.mark.asyncio
async def test_llama_client_sends_expected_payload_with_model_and_messages() -> None:
    captured_payload: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_payload
        captured_payload = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Короткий ответ"}}]},
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as mock_client:
        client = LlamaClient(base_url="http://127.0.0.1:8012", model="Qwen")

        original_async_client = httpx.AsyncClient

        class _PatchedClient:
            def __init__(self, *args, **kwargs):
                self._client = mock_client

            async def __aenter__(self):
                return self._client

            async def __aexit__(self, exc_type, exc, tb):
                return False

        httpx.AsyncClient = _PatchedClient  # type: ignore[assignment]
        try:
            result = await client.generate_reply([{"role": "user", "content": "Привет"}])
        finally:
            httpx.AsyncClient = original_async_client  # type: ignore[assignment]

    assert result == "Короткий ответ"
    assert captured_payload["model"] == "Qwen"
    assert captured_payload["messages"] == [{"role": "user", "content": "Привет"}]
