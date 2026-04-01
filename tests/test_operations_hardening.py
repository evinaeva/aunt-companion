from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.asyncio
async def test_app_run_initializes_and_closes_connection(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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

    calls: list[str] = []

    async def fake_initialize_database(**kwargs):
        assert kwargs["db_path"] == db_path
        calls.append("initialize_database")

    class FakeConn:
        closed = False

        async def close(self) -> None:
            self.closed = True
            calls.append("close")

    fake_conn = FakeConn()

    async def fake_connect(path: Path) -> FakeConn:
        assert path == db_path
        calls.append("connect")
        return fake_conn

    async def fake_run_polling(_settings, _conn) -> None:
        calls.append("run_polling")

    monkeypatch.setattr(app_main, "get_settings", lambda: settings)
    monkeypatch.setattr(app_main, "configure_logging", lambda *_: None)
    monkeypatch.setattr(app_main, "initialize_database", fake_initialize_database)
    monkeypatch.setattr(app_main, "connect", fake_connect)
    monkeypatch.setattr(app_main, "run_polling", fake_run_polling)

    await app_main._run()

    assert calls == ["initialize_database", "connect", "run_polling", "close"]
    assert fake_conn.closed is True


@pytest.mark.asyncio
async def test_text_handler_falls_back_when_llama_client_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.telegram import handlers

    class DummyUsersRepository:
        def __init__(self, _conn):
            return None

        async def get_or_create_user(self, **kwargs):
            return SimpleNamespace(id=77)

    class DummyConversationsRepository:
        def __init__(self, _conn):
            return None

        async def get_latest_for_user(self, _user_id):
            return None

        async def create_conversation(self, _user_id, title):
            return SimpleNamespace(id=55, title=title)

    class DummyMessagesRepository:
        def __init__(self, _conn):
            self.saved_texts: list[str] = []

        async def add_message(self, **kwargs):
            self.saved_texts.append(kwargs["text"])
            return SimpleNamespace(id=101)

        async def list_recent_by_user(self, _user_id, limit=10):
            return []

    monkeypatch.setattr(handlers, "UsersRepository", DummyUsersRepository)
    monkeypatch.setattr(handlers, "ConversationsRepository", DummyConversationsRepository)
    monkeypatch.setattr(handlers, "MessagesRepository", DummyMessagesRepository)
    monkeypatch.setattr(handlers, "load_system_prompt_ru", lambda: "system")
    monkeypatch.setattr(
        handlers,
        "build_chat_messages",
        lambda **kwargs: [{"role": "user", "content": kwargs["current_user_text"]}],
    )

    class FailingClient:
        async def generate_reply(self, _messages):
            raise RuntimeError("llama down")

    answers: list[str] = []

    async def answer(text: str) -> None:
        answers.append(text)

    message = SimpleNamespace(
        text="Привет",
        from_user=SimpleNamespace(id=7, full_name="User"),
        message_id=99,
        answer=answer,
    )

    await handlers.text_message_handler(message, db_conn=object(), llm_client=FailingClient())

    assert answers
    assert "Попробуйте ещё раз чуть позже" in answers[-1]


@pytest.mark.asyncio
async def test_run_polling_wires_dispatcher_and_client(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.telegram import bot as telegram_bot

    call_log: dict[str, object] = {}

    class FakeBot:
        def __init__(self, token: str) -> None:
            call_log["token"] = token
            self.session = SimpleNamespace(close=self._close)
            self.closed = False

        async def _close(self) -> None:
            self.closed = True
            call_log["bot_closed"] = True

    class FakeMessagePipeline:
        def middleware(self, mw):
            call_log["middleware"] = mw

    class FakeDispatcher:
        def __init__(self) -> None:
            self.message = FakeMessagePipeline()

        def include_router(self, router):
            call_log["router"] = router

        async def start_polling(self, bot, **kwargs):
            call_log["polling_kwargs"] = kwargs
            call_log["polling_bot"] = bot

    class FakeChatClient:
        pass

    def fake_build_primary_chat_client(passed_settings):
        call_log["selected_settings"] = passed_settings
        call_log["llm_provider"] = passed_settings.llm.provider
        call_log["llm_base_url"] = passed_settings.llm.base_url
        call_log["llm_model"] = passed_settings.llm.model
        return FakeChatClient()

    settings = SimpleNamespace(
        telegram=SimpleNamespace(bot_token="token", allowed_user_ids=[1, 2]),
        llm=SimpleNamespace(provider="llama_cpp", base_url="http://127.0.0.1:8012", model="Qwen"),
        stt=SimpleNamespace(provider="faster_whisper", model="small", compute_type="int8", language="ru"),
        tts=SimpleNamespace(
            provider="google_cloud",
            language_code="ru-RU",
            voice_name="",
            voice_gender="FEMALE",
            audio_encoding="OGG_OPUS",
        ),
        voice=SimpleNamespace(stt_provider="faster_whisper", tts_provider="google_cloud"),
        recent_context_messages=4,
        paths=SimpleNamespace(tmp_dir=Path("/tmp")),
    )

    monkeypatch.setattr(telegram_bot, "Bot", FakeBot)
    monkeypatch.setattr(telegram_bot, "Dispatcher", FakeDispatcher)
    monkeypatch.setattr(telegram_bot, "build_primary_chat_client", fake_build_primary_chat_client)

    await telegram_bot.run_polling(settings, db_conn="db_conn")

    assert call_log["token"] == "token"
    assert call_log["llm_base_url"] == "http://127.0.0.1:8012"
    assert call_log["llm_model"] == "Qwen"
    assert call_log["polling_kwargs"]["db_conn"] == "db_conn"
    assert call_log["polling_kwargs"]["llm_client"] is not None
    assert call_log["polling_kwargs"]["stt_adapter"] is not None
    assert call_log["polling_kwargs"]["tts_adapter"] is not None
    assert call_log["bot_closed"] is True


def test_settings_paths_are_loaded_for_server_execution(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from app.config import Settings

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "000:token")
    monkeypatch.setenv("ALLOWED_TELEGRAM_USER_IDS", "1,2")
    monkeypatch.setenv("ADMIN_TELEGRAM_USER_ID", "1")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:8012")
    monkeypatch.setenv("LLM_MODEL", "Qwen")
    monkeypatch.setenv("STT_MODEL", "small")
    monkeypatch.setenv("STT_COMPUTE_TYPE", "int8")
    monkeypatch.setenv("TTS_PROVIDER", "google_cloud")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("TMP_DIR", str(tmp_path / "data" / "tmp"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "data" / "logs"))
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "data" / "db" / "gosha.sqlite3"))

    settings = Settings()

    assert settings.paths.data_dir == tmp_path / "data"
    assert settings.paths.tmp_dir == tmp_path / "data" / "tmp"
    assert settings.paths.log_dir == tmp_path / "data" / "logs"
    assert settings.paths.sqlite_path == tmp_path / "data" / "db" / "gosha.sqlite3"
