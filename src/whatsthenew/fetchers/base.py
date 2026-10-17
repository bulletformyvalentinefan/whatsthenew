"""Utilidades HTTP compartidas: cliente con pausas anti-bloqueo."""

from __future__ import annotations

import time

import httpx


class HttpClient:
    """Cliente httpx que respeta una pausa mínima entre peticiones.

    La pausa por defecto (4 s) evita bloqueos por ráfaga (429/403).
    """

    def __init__(self, user_agent: str, delay: float = 4.0, timeout: float = 25.0) -> None:
        self._delay = delay
        self._last = 0.0
        self._client = httpx.Client(
            headers={"User-Agent": user_agent, "Accept": "*/*"},
            timeout=timeout,
            follow_redirects=True,
        )

    def _wait(self) -> None:
        elapsed = time.monotonic() - self._last
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)

    def get(self, url: str, **kwargs) -> httpx.Response:
        self._wait()
        resp = self._client.get(url, **kwargs)
        self._last = time.monotonic()
        resp.raise_for_status()
        return resp

    def get_text(self, url: str, **kwargs) -> str:
        return self.get(url, **kwargs).text

    def get_json(self, url: str, **kwargs):
        return self.get(url, **kwargs).json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
