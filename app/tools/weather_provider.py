"""Weather provider abstraction and Open-Meteo implementation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import urlopen
import json

from app.tools.models import WeatherData


class WeatherProvider(Protocol):
    async def get_weather(self, *, location: str) -> WeatherData:
        """Return compact weather snapshot for location."""


@dataclass(slots=True)
class OpenMeteoWeatherProvider:
    """Weather provider backed by Open-Meteo geocoding + forecast endpoints."""

    timeout_seconds: float = 8.0

    async def get_weather(self, *, location: str) -> WeatherData:
        geo_params = urlencode({"name": location, "count": 1, "language": "en", "format": "json"})
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?{geo_params}"
        with urlopen(geo_url, timeout=self.timeout_seconds) as response:  # noqa: S310
            geocode_payload = json.load(response)

        results = geocode_payload.get("results") or []
        if not results:
            raise ValueError(f"Unknown location: {location}")

        best = results[0]
        lat = best["latitude"]
        lon = best["longitude"]
        resolved_name = best.get("name") or location

        weather_params = urlencode(
            {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code",
                "timezone": "auto",
            }
        )
        weather_url = f"https://api.open-meteo.com/v1/forecast?{weather_params}"
        with urlopen(weather_url, timeout=self.timeout_seconds) as response:  # noqa: S310
            weather_payload = json.load(response)

        current = weather_payload.get("current") or {}
        observed_at = datetime.fromisoformat(current["time"]).replace(tzinfo=UTC)
        weather_code = int(current.get("weather_code", -1))

        return WeatherData(
            location=resolved_name,
            timezone=weather_payload.get("timezone", "UTC"),
            observed_at=observed_at,
            temperature_c=float(current["temperature_2m"]),
            condition=_WEATHER_CODE_LABELS.get(weather_code, "unknown"),
        )


_WEATHER_CODE_LABELS = {
    0: "clear",
    1: "mainly_clear",
    2: "partly_cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing_rime_fog",
    51: "light_drizzle",
    53: "moderate_drizzle",
    55: "dense_drizzle",
    61: "slight_rain",
    63: "moderate_rain",
    65: "heavy_rain",
    71: "slight_snow",
    73: "moderate_snow",
    75: "heavy_snow",
    80: "rain_showers",
    95: "thunderstorm",
}
