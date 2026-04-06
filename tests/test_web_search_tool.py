from datetime import UTC, datetime

import pytest

from app.llm.tool_context import ToolRequestContext
from app.tools.models import SearchResult
from app.tools.web_search_tool import build_web_search_tool


class FakeSearchProvider:
    async def search(self, *, query: str, limit: int) -> list[SearchResult]:
        assert query == "latest mars mission"
        assert limit == 2
        return [
            SearchResult(title="Result 1", url="https://example.com/1", snippet="A" * 300),
            SearchResult(title="Result 2", url="https://example.com/2", snippet="B" * 20),
            SearchResult(title="Result 3", url="https://example.com/3", snippet="C" * 20),
        ]


@pytest.mark.asyncio
async def test_web_search_tool_returns_bounded_compact_results() -> None:
    tool = build_web_search_tool(provider=FakeSearchProvider())
    context = ToolRequestContext(
        user_id=1,
        telegram_user_id=1,
        now_utc=datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
    )

    result = await tool.handler(context, {"query": "latest mars mission", "limit": 2})

    assert result["query"] == "latest mars mission"
    assert len(result["results"]) == 2
    assert result["results"][0]["title"] == "Result 1"
    assert len(result["results"][0]["snippet"]) == 240
