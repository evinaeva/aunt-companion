"""Executable web-search tool binding."""

from __future__ import annotations

from dataclasses import dataclass

from app.llm.tool_context import ToolRequestContext
from app.llm.tool_contracts import RegisteredTool, ToolDefinition
from app.tools.web_search_provider import DuckDuckGoWebSearchProvider, WebSearchProvider

_MAX_RESULTS = 5


@dataclass(slots=True)
class WebSearchTool:
    provider: WebSearchProvider

    async def __call__(self, context: ToolRequestContext, arguments: dict[str, object]) -> dict[str, object]:
        query = str(arguments.get("query") or "").strip()
        if not query:
            raise ValueError("query is required")

        requested_limit = int(arguments.get("limit") or 3)
        limit = max(1, min(requested_limit, _MAX_RESULTS))
        results = await self.provider.search(query=query, limit=limit)

        return {
            "query": query,
            "results": [
                {
                    "title": item.title[:100],
                    "url": item.url,
                    "snippet": item.snippet[:240],
                }
                for item in results[:limit]
            ],
        }


def build_web_search_tool(provider: WebSearchProvider | None = None) -> RegisteredTool:
    return RegisteredTool(
        definition=ToolDefinition(
            name="web_search",
            description="Search the web for recent references.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query text."},
                    "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_RESULTS, "default": 3},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        ),
        handler=WebSearchTool(provider=provider or DuckDuckGoWebSearchProvider()),
    )
