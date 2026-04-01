"""Shared contracts for model-visible tools and executable tool bindings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Protocol
from typing import Sequence

from app.llm.tool_context import ToolRequestContext


@dataclass(slots=True, frozen=True)
class ToolDefinition:
    """Model-visible tool definition independent from concrete implementations."""

    name: str
    description: str
    input_schema: dict[str, Any]


class ToolHandler(Protocol):
    """Async handler used by runtime to execute a tool call."""

    async def __call__(self, context: ToolRequestContext, arguments: dict[str, Any]) -> Any:
        """Execute the tool with request context and model-provided arguments."""


@dataclass(slots=True, frozen=True)
class RegisteredTool:
    """Executable tool binding for runtime orchestration."""

    definition: ToolDefinition
    handler: ToolHandler


class ToolsetFactory(Protocol):
    """Factory returning request-scoped executable tool bindings."""

    def __call__(self, context: ToolRequestContext) -> Sequence[RegisteredTool]:
        """Build registered tools available for the current request."""
