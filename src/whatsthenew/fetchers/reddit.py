"""Cliente de Reddit.

Flujo (en orden):
1. **Login**: `authenticate()` obtiene un token con el grant `client_credentials`
   (solo app id + secret, nunca una contraseña de usuario).
2. **Búsqueda**: `search()` usa el token y espera `delay` segundos entre consultas
   (por defecto 10 s) para no ser bloqueado.

Sin credenciales, cae automáticamente al modo **RSS** (con la misma pausa).
Ningún endpoint está escrito en el código: todos vienen de la configuración
(variables de entorno), porque el repositorio es público.
"""

from __future__ import annotations

import logging
import time
from urllib.parse import urlencode

import feedparser
import httpx

from ..config import (
    DEFAULT_REDDIT_OAUTH_BASE,
    DEFAULT_REDDIT_TOKEN_URL,
    DEFAULT_REDDIT_WWW_BASE,
)
from ..models import Item

log = logging.getLogger("whatsthenew.reddit")


class RedditClient:
    def __init__(
        self,
        user_agent: str,
        client_id: str = "",
        client_secret: str = "",
        delay: float = 10.0,
        limit: int = 15,
        timeout: float = 25.0,
        token_url: str = DEFAULT_REDDIT_TOKEN_URL,
        oauth_base: str = DEFAULT_REDDIT_OAUTH_BASE,
        www_base: str = DEFAULT_REDDIT_WWW_BASE,
    ) -> None:
        self.user_agent = user_agent
        self.client_id = client_id
        self.client_secret = client_secret
        self.delay = delay
        self.limit = limit
        self.timeout = timeout
        self.token_url = token_url
        self.oauth_base = oauth_base
        self.www_base = www_base

        self._token: str | None = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------ #
    # Paso 1: LOGIN
    # ------------------------------------------------------------------ #
    @property
    def has_credentials(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def authenticate(self) -> bool:
        """Obtiene un token de aplicación. Devuelve True si quedó autenticado."""
        if not self.has_credentials:
            log.info("Reddit sin credenciales: se usará el modo RSS.")
            return False

        try:
            resp = httpx.post(
                self.token_url,
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            log.warning("Reddit login falló (red): %s", exc)
            return False

        if resp.status_code != 200:
            log.warning("Reddit login rechazado (%s). Se usará RSS.", resp.status_code)
            return False

        payload = resp.json()
        token = payload.get("access_token")
        if not token:
            log.warning("Reddit login sin access_token en la respuesta.")
            return False

        expires_in = int(payload.get("expires_in", 3600))
        self._token = token
        self._token_expiry = time.monotonic() + max(expires_in - 60, 60)
        log.info("Reddit autenticado (token válido ~%s s).", expires_in)
        return True

    def _ensure_token(self) -> str | None:
        """Devuelve un token válido, reautenticando si expiró."""
        if self._token and time.monotonic() < self._token_expiry:
            return self._token
        self.authenticate()
        return self._token

    # ------------------------------------------------------------------ #
    # Paso 2: BÚSQUEDA
    # ------------------------------------------------------------------ #
    def search(
        self,
        sub: str,
        query: str,
        t: str = "month",
        sort: str = "top",
        limit: int | None = None,
    ) -> list[Item]:
        """Busca en un subreddit y espera `delay` segundos antes de volver."""
        limit = limit or self.limit
        token = self._ensure_token()

        try:
            items = (
                self._search_oauth(sub, query, t, sort, limit, token)
                if token
                else self._search_rss(sub, query, t, sort, limit)
            )
        finally:
            # Pausa de 10 s entre búsquedas (aplica a ambos modos).
            time.sleep(self.delay)
        return items

    def _search_oauth(self, sub: str, query: str, t: str, sort: str, limit: int, token: str) -> list[Item]:
        url = f"{self.oauth_base}/r/{sub}/search"
        params = {"q": query, "restrict_sr": 1, "sort": sort, "t": t, "limit": limit}
        headers = {"Authorization": f"Bearer {token}", "User-Agent": self.user_agent}
        resp = httpx.get(url, params=params, headers=headers, timeout=self.timeout)

        if resp.status_code == 401:  # token vencido a mitad de camino
            self._token = None
            token = self._ensure_token()
            if not token:
                return self._search_rss(sub, query, t, sort, limit)
            headers["Authorization"] = f"Bearer {token}"
            resp = httpx.get(url, params=params, headers=headers, timeout=self.timeout)

        if resp.status_code != 200:
            log.warning("Reddit search (%s) devolvió %s", sub, resp.status_code)
            return []

        out: list[Item] = []
        for child in resp.json().get("data", {}).get("children", []):
            d = child.get("data", {})
            out.append(
                Item(
                    category="reddit",
                    source=f"reddit.com/r/{sub}",
                    source_type="reddit",
                    url=f"{self.www_base}{d.get('permalink', '')}",
                    title=d.get("title", ""),
                    posted_at=str(d.get("created_utc", "")),
                    query=query,
                    excerpt=(d.get("selftext", "") or "")[:2000],
                )
            )
        return out

    def _search_rss(self, sub: str, query: str, t: str, sort: str, limit: int) -> list[Item]:
        params = urlencode({"q": query, "restrict_sr": 1, "sort": sort, "t": t})
        url = f"{self.www_base}/r/{sub}/search.rss?{params}"
        parsed = feedparser.parse(url, request_headers={"User-Agent": self.user_agent})
        out: list[Item] = []
        for e in parsed.entries[:limit]:
            out.append(
                Item(
                    category="reddit",
                    source=f"reddit.com/r/{sub}",
                    source_type="reddit",
                    url=e.get("link", ""),
                    title=e.get("title", ""),
                    posted_at=e.get("published", ""),
                    query=query,
                    excerpt=(e.get("summary", "") or "")[:2000],
                )
            )
        return out
