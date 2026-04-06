"""Shared models for concrete tool providers and services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class WeatherData:
    location: str
    timezone: str
    observed_at: datetime
    temperature_c: float
    condition: str


@dataclass(slots=True, frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


@dataclass(slots=True, frozen=True)
class Reminder:
    id: int
    user_id: int
    title: str
    remind_at_utc: datetime
    timezone: str
    status: str
    created_at: datetime
