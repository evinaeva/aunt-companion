"""Executable weather tool binding."""

from __future__ import annotations

from dataclasses import dataclass

from app.llm.tool_context import ToolRequestContext
from app.llm.tool_contracts import RegisteredTool, ToolDefinition
from app.tools.weather_provider import OpenMeteoWeatherProvider, WeatherProvider


@dataclass(slots=True)
class WeatherTool:
    provider: WeatherProvider

    async def __call__(self, context: ToolRequestContext, arguments: dict[str, object]) -> dict[str, object]:
        location = str(arguments.get("location") or "").strip()
        if not location:
            raise ValueError("location is required")

        weather = await self.provider.get_weather(location=location)
        return {
            "location": weather.location,
            "timezone": weather.timezone,
            "observed_at": weather.observed_at.isoformat(),
            "temperature_c": round(weather.temperature_c, 1),
            "condition": weather.condition,
        }


def build_weather_tool(provider: WeatherProvider | None = None) -> RegisteredTool:
    return RegisteredTool(
        definition=ToolDefinition(
            name="weather",
            description="Get current weather for a location.",
            input_schema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City or place name."},
                },
                "required": ["location"],
                "additionalProperties": False,
            },
        ),
        handler=WeatherTool(provider=provider or OpenMeteoWeatherProvider()),
    )
