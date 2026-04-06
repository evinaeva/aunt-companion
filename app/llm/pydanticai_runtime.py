"""Tool-capable runtime that orchestrates model responses and tool execution."""

from __future__ import annotations

import json
import logging
from typing import Any, Sequence

from app.llm.base import ChatClient, LLMResponse, ToolInvocation
from app.llm.tool_context import ToolRequestContext
from app.llm.tool_contracts import RegisteredTool

logger = logging.getLogger(__name__)


class PydanticAIToolRuntime:
    """Runtime that supports optional tool execution on top of existing chat adapters."""

    def __init__(self, llm_client: ChatClient, *, max_tool_rounds: int = 4) -> None:
        self._llm_client = llm_client
        self._max_tool_rounds = max_tool_rounds

    async def generate(
        self,
        messages: list[dict[str, str]],
        *,
        request_context: ToolRequestContext,
        tools: Sequence[RegisteredTool],
    ) -> LLMResponse:
        if not tools:
            return await self._llm_client.generate(messages)

        registered_tools = {tool.definition.name: tool for tool in tools}
        tool_messages = self._with_tool_definitions(messages, tools)
        all_invocations: list[ToolInvocation] = []

        for _ in range(self._max_tool_rounds):
            response = await self._llm_client.generate(tool_messages)
            if not response.tool_invocations:
                if all_invocations:
                    return LLMResponse(
                        text=response.text,
                        tool_invocations=tuple(all_invocations),
                        is_fallback=response.is_fallback,
                        raw=response.raw,
                    )
                return response

            all_invocations.extend(response.tool_invocations)
            tool_messages.append({"role": "assistant", "content": response.text or ""})
            for invocation in response.tool_invocations:
                handler = registered_tools.get(invocation.tool_name)
                if handler is None:
                    tool_result: Any = {
                        "error": f"unknown tool: {invocation.tool_name}",
                        "tool_name": invocation.tool_name,
                    }
                else:
                    tool_result = await handler.handler(request_context, invocation.arguments)
                tool_messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(
                            {
                                "tool_name": invocation.tool_name,
                                "call_id": invocation.call_id,
                                "result": tool_result,
                            },
                            ensure_ascii=False,
                        ),
                    }
                )

        logger.warning(
            "Tool runtime reached max rounds; returning safe fallback",
            extra={"tool_rounds": self._max_tool_rounds, "tool_count": len(tools)},
        )
        return LLMResponse(
            text="Сейчас не получается корректно завершить запрос. Попробуй переформулировать.",
            tool_invocations=tuple(all_invocations),
            is_fallback=True,
        )

    async def generate_reply(self, messages: list[dict[str, str]]) -> str:
        response = await self._llm_client.generate(messages)
        return response.text

    def _with_tool_definitions(self, messages: list[dict[str, str]], tools: Sequence[RegisteredTool]) -> list[dict[str, str]]:
        rendered_tools = [
            {
                "name": tool.definition.name,
                "description": tool.definition.description,
                "input_schema": tool.definition.input_schema,
            }
            for tool in tools
        ]
        tool_instruction = (
            "Доступные инструменты (используй только при необходимости): "
            + json.dumps(rendered_tools, ensure_ascii=False)
        )
        return [*messages, {"role": "system", "content": tool_instruction}]
