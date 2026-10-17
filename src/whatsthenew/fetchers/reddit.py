"""Cliente de Reddit.

Modo por defecto: **RSS**, sin credenciales (no requiere cuenta ni aprobación).

- **Búsqueda**: `search()` lista los hilos de un subreddit (tema, fecha, url) y
  espera `delay` segundos entre consultas.
- **Respuestas**: `thread_replies()` mira el feed de comentarios de un hilo y
  cuenta cuántas respuestas tiene.

Opcional: si algún día se aprueba el acceso a la API, `authenticate()` hace el
login OAuth `client_credentials` y `search()` usa el endpoint OAuth en vez del
RSS. No es necesario para funcionar.

Los endpoints no están escritos aquí: vienen de la configuración (variables de
entorno), porque el repositorio es público.
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
        retries: int = 2,
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
        self.retries = max(retries, 0)
        self.token_url = token_url
        self.oauth_base = oauth_base
        self.www_base = www_base

        self._token: str | None = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------ #
    # Login OAuth (opcional, solo si hay credenciales)
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
    # Ritmo entre peticiones
    # ------------------------------------------------------------------ #
    def _pace(self) -> None:
        """Espera `delay` segundos. Corre semanal: tardar no es problema."""
        time.sleep(self.delay)

    # ------------------------------------------------------------------ #
    # Búsqueda de hilos
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
            self._pace()
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
        parsed = self._get_feed(url)
        if parsed is None:
            return []

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

    # ------------------------------------------------------------------ #
    # Respuestas de un hilo
    # ------------------------------------------------------------------ #
    @staticmethod
    def _comments_feed_url(permalink: str) -> str:
        """Convierte el permalink de un hilo en la URL de su feed de comentarios."""
        return f"{permalink.rstrip('/')}/.rss"

    @staticmethod
    def _reply_stats(parsed) -> tuple[int, bool]:
        """Cuenta respuestas en un feed de comentarios.

        La primera entrada suele ser el propio post, por eso se resta 1.
        """
        entries = getattr(parsed, "entries", None) or []
        replies = max(len(entries) - 1, 0)
        return replies, replies > 0

    def thread_replies(self, permalink: str) -> tuple[int, bool]:
        """Devuelve (número de respuestas, si tiene respuestas) de un hilo."""
        if not permalink:
            return 0, False
        parsed = self._get_feed(self._comments_feed_url(permalink))
        self._pace()
        if parsed is None:
            return 0, False
        return self._reply_stats(parsed)

    # ------------------------------------------------------------------ #
    # Descarga de feeds con backoff ante 429
    # ------------------------------------------------------------------ #
    def _get_feed(self, url: str):
        """Descarga un feed RSS con reintentos y espera creciente ante 429."""
        attempts = self.retries + 1
        for attempt in range(attempts):
            parsed = feedparser.parse(url, request_headers={"User-Agent": self.user_agent})
            status = int(getattr(parsed, "status", 200) or 200)
            if status == 429:
                wait = self.delay * (attempt + 1)
                log.warning(
                    "Reddit 429 (%s); reintento %d/%d en %.0f s", url, attempt + 1, attempts, wait
                )
                time.sleep(wait)
                continue
            if status >= 400:
                log.warning("Reddit %s en %s", status, url)
                return None
            return parsed
        log.warning("Reddit sigue en 429 tras %d intentos: %s", attempts, url)
        return None
