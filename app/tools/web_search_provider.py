"""Web-search provider abstraction and DuckDuckGo implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import urlopen
import json

from app.tools.models import SearchResult


class WebSearchProvider(Protocol):
    async def search(self, *, query: str, limit: int) -> list[SearchResult]:
        """Search web and return normalized result items."""


@dataclass(slots=True)
class DuckDuckGoWebSearchProvider:
    """Simple web search provider using DuckDuckGo Instant Answer API."""

    timeout_seconds: float = 8.0

    async def search(self, *, query: str, limit: int) -> list[SearchResult]:
        params = urlencode({"q": query, "format": "json", "no_html": 1, "skip_disambig": 1})
        url = f"https://api.duckduckgo.com/?{params}"

        with urlopen(url, timeout=self.timeout_seconds) as response:  # noqa: S310
            payload = json.load(response)

        output: list[SearchResult] = []
        related = payload.get("RelatedTopics") or []
        for item in related:
            if "Topics" in item:
                for topic in item["Topics"]:
                    parsed = _parse_topic(topic)
                    if parsed is not None:
                        output.append(parsed)
            else:
                parsed = _parse_topic(item)
                if parsed is not None:
                    output.append(parsed)
            if len(output) >= limit:
                break

        return output[:limit]


def _parse_topic(topic: dict[str, object]) -> SearchResult | None:
    text = str(topic.get("Text") or "").strip()
    first_url = str(topic.get("FirstURL") or "").strip()
    if not text or not first_url:
        return None

    title = text.split(" - ", 1)[0][:100]
    snippet = text[:240]
    return SearchResult(title=title, url=first_url, snippet=snippet)
