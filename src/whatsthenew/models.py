"""Modelo de datos común a todas las fuentes.

Cada Item lleva SIEMPRE de dónde salió (source/url) y cuándo se consultó
(fetched_at) además de cuándo se publicó el dato (posted_at).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def now_local_iso() -> str:
    """Fecha de consulta con zona local, formato ISO (para trazabilidad)."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class Item:
    category: str  # jobs | news | company_blog | reddit | roadmap
    source: str  # dominio o id de la fuente
    source_type: str  # api | rss | html | xml | reddit
    url: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    remote: Optional[bool] = None
    role: str = ""
    level: str = ""
    years: list[int] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    salary: str = ""
    applicants: str = ""
    posted_at: str = ""
    fetched_at: str = field(default_factory=now_local_iso)
    query: str = ""
    excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def items_to_payload(items: list[Item], meta: dict[str, Any]) -> dict[str, Any]:
    return {"meta": meta, "items": [i.to_dict() for i in items]}
