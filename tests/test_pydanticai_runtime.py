from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.llm.base import LLMResponse, ToolInvocation
from app.llm.pydanticai_runtime import PydanticAIToolRuntime
from app.llm.tool_context import ToolRequestContext
from app.llm.tool_contracts import RegisteredTool, ToolDefinition


class _SequenceClient:
    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = responses
        self.calls: list[list[dict[str, str]]] = []

    async def generate(self, messages: list[dict[str, str]]) -> LLMResponse:
        self.calls.append(messages)
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_runtime_empty_toolset_passes_through() -> None:
    client = _SequenceClient([LLMResponse(text="Простой ответ")])
    runtime = PydanticAIToolRuntime(client)

    response = await runtime.generate(
        [{"role": "user", "content": "Привет"}],
        request_context=ToolRequestContext(user_id=1, telegram_user_id=101, now_utc=datetime(2026, 4, 1, tzinfo=UTC)),
        tools=(),
    )

    assert response.text == "Простой ответ"
    assert len(client.calls) == 1
    assert client.calls[0] == [{"role": "user", "content": "Привет"}]


@pytest.mark.asyncio
async def test_runtime_executes_registered_tool_and_preserves_invocation() -> None:
    calls: list[dict[str, object]] = []

    async def fake_tool(context: ToolRequestContext, arguments: dict[str, object]) -> dict[str, object]:
        calls.append({"user_id": context.user_id, **arguments})
        return {"echo": arguments["value"]}

    tool = RegisteredTool(
        definition=ToolDefinition(
            name="echo_tool",
            description="Echo argument",
            input_schema={"type": "object", "properties": {"value": {"type": "string"}}},
        ),
        handler=fake_tool,
    )
    client = _SequenceClient(
        [
            LLMResponse(
                text="",
                tool_invocations=(ToolInvocation(tool_name="echo_tool", arguments={"value": "ok"}, call_id="c1"),),
            ),
            LLMResponse(text="Готово"),
        ]
    )
    runtime = PydanticAIToolRuntime(client)

    response = await runtime.generate(
        [{"role": "user", "content": "Сделай"}],
        request_context=ToolRequestContext(user_id=7, telegram_user_id=77, now_utc=datetime(2026, 4, 1, tzinfo=UTC)),
        tools=(tool,),
    )

    assert response.text == "Готово"
    assert response.tool_invocations[0].tool_name == "echo_tool"
    assert calls == [{"user_id": 7, "value": "ok"}]
    assert any("echo_tool" in message["content"] for message in client.calls[0] if message["role"] == "system")
