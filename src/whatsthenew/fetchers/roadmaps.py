"""Fetchers de roadmaps y tendencias de skills."""

from __future__ import annotations

from ..models import Item
from .base import HttpClient


def fetch_devto(client: HttpClient, url: str) -> list[Item]:
    data = client.get_json(url)
    items: list[Item] = []
    for a in data:
        items.append(Item(
            category="roadmap",
            source="dev.to",
            source_type="api",
            url=a.get("url", ""),
            title=a.get("title", ""),
            posted_at=str(a.get("published_at", "")),
            excerpt=(a.get("description", "") or "")[:2000],
        ))
    return items


def fetch_github_repo(client: HttpClient, repo: str, branch: str = "master", api_base: str = "") -> list[Item]:
    """Lista el contenido de un repositorio (roadmap.sh) sin clonar.

    `api_base` se inyecta desde la configuración (no se escribe aquí).
    """
    base = api_base.rstrip("/")
    url = f"{base}/repos/{repo}/contents/roadmaps?ref={branch}"
    data = client.get_json(url)
    items: list[Item] = []
    for entry in data:
        if entry.get("type") != "dir":
            continue
        items.append(Item(
            category="roadmap",
            source=f"github.com/{repo}",
            source_type="api",
            url=entry.get("html_url", ""),
            title=entry.get("name", ""),
        ))
    return items
