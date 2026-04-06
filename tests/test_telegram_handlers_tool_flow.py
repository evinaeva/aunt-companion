from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.db import MessagesRepository, UsersRepository, connect, initialize_database
from app.llm.base import LLMResponse
from app.telegram import dependencies
from app.telegram.handlers import text_message_handler, voice_message_handler


class _FakeRuntime:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls: list[dict[str, object]] = []

    async def generate(self, messages, *, request_context, tools):
        self.calls.append({"messages": messages, "request_context": request_context, "tools": tuple(tools)})
        return LLMResponse(text=self.response_text)


@pytest.mark.asyncio
async def test_text_message_flow_uses_tool_capable_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "runtime" / "data" / "db" / "gosha.sqlite3"
    await initialize_database(
        db_path=db_path,
        data_dir=tmp_path / "runtime" / "data",
        tmp_dir=tmp_path / "runtime" / "tmp",
        log_dir=tmp_path / "runtime" / "logs",
    )
    conn = await connect(db_path)
    runtime = _FakeRuntime("Ответ")
    monkeypatch.setattr("app.telegram.handlers.build_tool_runtime", lambda llm_client: runtime)
    monkeypatch.setattr("app.telegram.handlers.get_toolset_factory", lambda: (lambda context: ()))

    msg = SimpleNamespace(
        text="Привет",
        message_id=10,
        from_user=SimpleNamespace(id=501, full_name="User"),
        answer=AsyncMock(),
    )

    try:
        await text_message_handler(msg, conn, llm_client=SimpleNamespace())
        users_repo = UsersRepository(conn)
        messages_repo = MessagesRepository(conn)
        user = await users_repo.get_or_create_user(telegram_user_id=501, display_name="User", is_admin=False)
        persisted = await messages_repo.list_recent_by_user(user.id, limit=10)
    finally:
        await conn.close()

    assert len(runtime.calls) == 1
    assert msg.answer.await_args.args[0] == "Ответ"
    assert [item.direction for item in persisted] == ["outgoing", "incoming"]


@pytest.mark.asyncio
async def test_voice_transcript_flow_uses_same_runtime_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class _Proc:
        returncode = 0

        async def communicate(self):
            return b"", b""

    async def _fake_exec(*args, **kwargs):
        return _Proc()

    db_path = tmp_path / "runtime" / "data" / "db" / "gosha.sqlite3"
    await initialize_database(
        db_path=db_path,
        data_dir=tmp_path / "runtime" / "data",
        tmp_dir=tmp_path / "runtime" / "tmp",
        log_dir=tmp_path / "runtime" / "logs",
    )
    conn = await connect(db_path)

    runtime = _FakeRuntime("Голосовой ответ")
    monkeypatch.setattr("app.telegram.handlers.build_tool_runtime", lambda llm_client: runtime)
    monkeypatch.setattr("app.telegram.handlers.get_toolset_factory", lambda: (lambda context: ()))
    monkeypatch.setattr("app.telegram.handlers.shutil.which", lambda _: "/usr/bin/ffmpeg")
    monkeypatch.setattr("app.telegram.handlers.asyncio.create_subprocess_exec", _fake_exec)

    fake_bot = SimpleNamespace(
        get_file=AsyncMock(return_value=SimpleNamespace(file_path="voice.ogg")),
        download_file=AsyncMock(return_value=None),
    )
    message = SimpleNamespace(
        message_id=11,
        voice=SimpleNamespace(file_id="voice-file"),
        from_user=SimpleNamespace(id=700, full_name="Voice User"),
        bot=fake_bot,
        answer=AsyncMock(),
        answer_voice=AsyncMock(),
    )

    stt_adapter = SimpleNamespace(transcribe=AsyncMock(return_value="транскрипт"))
    tts_adapter = SimpleNamespace(synthesize=AsyncMock(return_value=b"voice"))

    try:
        await voice_message_handler(
            message,
            conn,
            llm_client=SimpleNamespace(),
            stt_adapter=stt_adapter,
            tts_adapter=tts_adapter,
            tmp_dir=tmp_path,
        )
    finally:
        await conn.close()

    assert len(runtime.calls) == 1
    assert runtime.calls[0]["messages"][-1]["content"] == "транскрипт"
    assert message.answer.await_args.args[0] == "Голосовой ответ"


def test_tool_factory_import_failure_falls_back_to_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    dependencies.set_toolset_factory(None)

    class _BadSettings:
        toolset_factory_import_path = "missing.module:factory"

    monkeypatch.setattr("app.telegram.dependencies.ToolSettings", _BadSettings)
    monkeypatch.setattr(
        "app.telegram.dependencies.load_toolset_factory",
        lambda _: (_ for _ in ()).throw(ValueError("boom")),
    )

    factory = dependencies.get_toolset_factory()

    assert factory(SimpleNamespace()) == ()
    dependencies.set_toolset_factory(None)
