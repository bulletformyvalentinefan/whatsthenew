"""Fetchers por familia de fuentes.

Cada fetcher recibe un HttpClient y la configuración de la fuente y devuelve
una lista de `Item`. Todos usan `classify()` para etiquetar el resultado.
"""

from __future__ import annotations

from .base import HttpClient
from .jobs import (
    fetch_getonbrd,
    fetch_hackernews_whoishiring,
    fetch_jobicy,
    fetch_json_board,
    fetch_rss_jobs,
    fetch_seek_jobs,
)
from .news import fetch_rss
from .reddit import RedditClient
from .roadmaps import fetch_devto, fetch_github_repo

__all__ = [
    "HttpClient",
    "RedditClient",
    "fetch_getonbrd",
    "fetch_seek_jobs",
    "fetch_jobicy",
    "fetch_json_board",
    "fetch_rss_jobs",
    "fetch_hackernews_whoishiring",
    "fetch_rss",
    "fetch_devto",
    "fetch_github_repo",
]
