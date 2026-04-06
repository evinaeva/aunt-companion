from datetime import UTC, datetime

from app.llm.tool_context import ToolRequestContext
from app.tools.factory import build_default_toolset_factory


def test_build_default_toolset_factory_exposes_expected_tools() -> None:
    context = ToolRequestContext(
        user_id=1,
        telegram_user_id=10,
        now_utc=datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
        metadata={"db_path": "/tmp/test.db"},
    )

    toolset = build_default_toolset_factory(context)

    assert [tool.definition.name for tool in toolset] == ["weather", "reminders", "web_search"]
