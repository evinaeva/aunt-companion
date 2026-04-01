"""Protocol for chat runtimes that support optional tool execution."""

from __future__ import annotations

from typing import Protocol
from typing import Sequence

from app.llm.base import LLMResponse
from app.llm.tool_context import ToolRequestContext
from app.llm.tool_contracts import RegisteredTool


class ToolCapableChatRuntime(Protocol):
    """Provider-agnostic chat runtime capable of handling model tool calls."""

    async def generate(
        self,
        messages: list[dict[str, str]],
        *,
        request_context: ToolRequestContext,
        tools: Sequence[RegisteredTool],
    ) -> LLMResponse:
        """Generate an assistant result with optional tool calls."""
