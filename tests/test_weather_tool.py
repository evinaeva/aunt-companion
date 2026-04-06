from datetime import UTC, datetime

import pytest

from app.llm.tool_context import ToolRequestContext
from app.tools.models import WeatherData
from app.tools.weather_tool import build_weather_tool


class FakeWeatherProvider:
    async def get_weather(self, *, location: str) -> WeatherData:
        assert location == "Berlin"
        return WeatherData(
            location="Berlin",
            timezone="Europe/Berlin",
            observed_at=datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
            temperature_c=12.34,
            condition="clear",
        )


@pytest.mark.asyncio
async def test_weather_tool_returns_compact_shape() -> None:
    tool = build_weather_tool(provider=FakeWeatherProvider())
    context = ToolRequestContext(
        user_id=1,
        telegram_user_id=1,
        now_utc=datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
    )

    result = await tool.handler(context, {"location": "Berlin"})

    assert result == {
        "location": "Berlin",
        "timezone": "Europe/Berlin",
        "observed_at": "2026-04-01T09:00:00+00:00",
        "temperature_c": 12.3,
        "condition": "clear",
    }
