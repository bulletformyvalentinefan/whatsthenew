"""Reddit vía PullPush: espejo público de Pushshift (sin login, sin credenciales).

Ventaja: en UNA petición devuelve tema, fecha y **nº de respuestas**
(`num_comments`), además del texto del post. Evita el bloqueo 403/429 que
Reddit aplica a los feeds RSS.

El endpoint es configurable (variable de entorno), no está escrito aquí.
"""

from __future__ import annotations

from urllib.parse import quote_plus

from ..models import Item
from .base import HttpClient

REDDIT_BASE = "https://www.reddit.com"


def fetch_pullpush(
    client: HttpClient,
    url_template: str,
    subreddit: str,
    query: str,
    size: int = 15,
) -> list[Item]:
    """Busca submissions en un subreddit y las mapea a `Item`."""
    url = url_template.format(subreddit=subreddit, query=quote_plus(query), size=size)
    payload = client.get_json(url)

    out: list[Item] = []
    for d in payload.get("data", []):
        permalink = d.get("permalink") or ""
        num = int(d.get("num_comments") or 0)
        out.append(
            Item(
                category="reddit",
                source=f"reddit.com/r/{d.get('subreddit', subreddit)}",
                source_type="pullpush",
                url=f"{REDDIT_BASE}{permalink}" if permalink else (d.get("full_link") or ""),
                title=d.get("title", ""),
                posted_at=str(d.get("created_utc", "")),
                query=query,
                replies=num,
                has_replies=num > 0,
                excerpt=(d.get("selftext", "") or "")[:2000],
            )
        )
    return out
