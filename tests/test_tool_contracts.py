from datetime import UTC, datetime

import pytest

from app.llm.base import LLMResponse, ToolInvocation
from app.llm.tool_context import ToolRequestContext
from app.llm.tool_contracts import RegisteredTool, ToolDefinition


def test_llm_response_defaults_keep_text_only_path() -> None:
    response = LLMResponse(text="Привет")

    assert response.text == "Привет"
    assert response.tool_invocations == ()
    assert response.raw is None


def test_tool_invocation_represents_model_requested_call() -> None:
    invocation = ToolInvocation(tool_name="get_weather", arguments={"city": "Moscow"}, call_id="call-1")

    assert invocation.tool_name == "get_weather"
    assert invocation.arguments == {"city": "Moscow"}
    assert invocation.call_id == "call-1"


@pytest.mark.asyncio
async def test_registered_tool_binds_definition_and_handler() -> None:
    async def _handler(context: ToolRequestContext, arguments: dict[str, object]) -> dict[str, object]:
        return {"tz": context.timezone, "echo": arguments}

    context = ToolRequestContext(
        user_id=7,
        telegram_user_id=77,
        now_utc=datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
        timezone="Europe/Moscow",
    )
    definition = ToolDefinition(
        name="echo",
        description="Echo arguments.",
        input_schema={"type": "object", "properties": {"value": {"type": "string"}}},
    )
    registered_tool = RegisteredTool(definition=definition, handler=_handler)

    result = await registered_tool.handler(context, {"value": "ok"})

    assert registered_tool.definition.name == "echo"
    assert result == {"tz": "Europe/Moscow", "echo": {"value": "ok"}}


def test_tool_request_context_has_timezone() -> None:
    now_utc = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)

    context = ToolRequestContext(user_id=7, telegram_user_id=77, now_utc=now_utc, timezone="Europe/Berlin")

    assert context.user_id == 7
    assert context.telegram_user_id == 77
    assert context.timezone == "Europe/Berlin"
    assert context.locale == "ru-RU"
