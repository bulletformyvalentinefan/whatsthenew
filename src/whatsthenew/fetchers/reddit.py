"""Cliente de Reddit: con token (OAuth, recomendado) o RSS (respaldo).

Reddit es la fuente más fuerte del proyecto, por eso se arma con cuidado:
- Con app OAuth gratuita (`client_credentials`): 100 peticiones/minuto.
- Sin token: RSS con pausas de 10 s (frágil, puede dar 429).
"""

from __future__ import annotations

import time

import feedparser
import httpx

from ..models import Item
from .base import HttpClient


class RedditClient:
    def __init__(
        self,
        user_agent: str,
        client_id: str = "",
        client_secret: str = "",
        delay: float = 10.0,
    ) -> None:
        self.user_agent = user_agent
        self.client_id = client_id
        self.client_secret = client_secret
        self.delay = delay
        self._token: str | None = None

    # --- OAuth ---------------------------------------------------------
    def _get_token(self) -> str | None:
        if not (self.client_id and self.client_secret):
            return None
        if self._token:
            return self._token
        resp = httpx.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(self.client_id, self.client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": self.user_agent},
            timeout=20,
        )
        if resp.status_code == 200:
            self._token = resp.json().get("access_token")
        return self._token

    # --- Búsqueda ------------------------------------------------------
    def search(
        self,
        sub: str,
        query: str,
        t: str = "month",
        sort: str = "top",
        limit: int = 15,
    ) -> list[Item]:
        token = self._get_token()
        if token:
            return self._search_oauth(sub, query, t, sort, limit, token)
        return self._search_rss(sub, query, t, sort)

    def _search_oauth(self, sub, query, t, sort, limit, token) -> list[Item]:
        url = f"https://oauth.reddit.com/r/{sub}/search"
        params = {"q": query, "restrict_sr": 1, "sort": sort, "t": t, "limit": limit}
        resp = httpx.get(url, params=params, headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": self.user_agent,
        }, timeout=25)
        time.sleep(self.delay / 10)  # OAuth permite mucho más ritmo
        if resp.status_code != 200:
            return []
        out: list[Item] = []
        for child in resp.json().get("data", {}).get("children", []):
            d = child.get("data", {})
            out.append(Item(
                category="reddit",
                source=f"reddit.com/r/{sub}",
                source_type="reddit",
                url=f"https://www.reddit.com{d.get('permalink', '')}",
                title=d.get("title", ""),
                posted_at=str(d.get("created_utc", "")),
                query=query,
                excerpt=(d.get("selftext", "") or "")[:2000],
            ))
        return out

    def _search_rss(self, sub, query, t, sort) -> list[Item]:
        url = f"https://www.reddit.com/r/{sub}/search.rss"
        params = {"q": query, "restrict_sr": 1, "sort": sort, "t": t}
        parsed = feedparser.parse(url, request_headers={"User-Agent": self.user_agent}, **{})
        time.sleep(self.delay)
        out: list[Item] = []
        for e in parsed.entries[:15]:
            out.append(Item(
                category="reddit",
                source=f"reddit.com/r/{sub}",
                source_type="reddit",
                url=e.get("link", ""),
                title=e.get("title", ""),
                posted_at=e.get("published", ""),
                query=query,
                excerpt=(e.get("summary", "") or "")[:2000],
            ))
        return out
