"""Request-scoped context shared across tool-enabled runtimes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True, frozen=True)
class ToolRequestContext:
    """Stable context describing a single assistant request."""

    user_id: int
    telegram_user_id: int
    now_utc: datetime
    timezone: str = "UTC"
    locale: str = "ru-RU"
    metadata: dict[str, Any] = field(default_factory=dict)
