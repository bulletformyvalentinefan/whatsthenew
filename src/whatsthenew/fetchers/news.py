"""Fetcher genérico de noticias y blogs por RSS."""

from __future__ import annotations

import feedparser

from ..models import Item
from .base import HttpClient


def fetch_rss(client: HttpClient, url: str, source: str, category: str = "news") -> list[Item]:
    parsed = feedparser.parse(client.get_text(url))
    items: list[Item] = []
    for e in parsed.entries[:40]:
        items.append(
            Item(
                category=category,
                source=source,
                source_type="rss",
                url=e.get("link", ""),
                title=e.get("title", ""),
                posted_at=e.get("published", ""),
                excerpt=(e.get("summary", "") or "")[:2000],
            )
        )
    return items
