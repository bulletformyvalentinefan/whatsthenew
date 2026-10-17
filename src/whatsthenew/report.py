"""Genera un reporte determinista (respaldo sin IA) agrupando por rol y nivel."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def _format_fetch_time() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def build_fallback_report(payload: dict[str, Any]) -> str:
    items = payload.get("items", [])
    by_role: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))

    for it in items:
        role = it.get("role") or it.get("title") or "(sin rol)"
        level = it.get("level") or "sin nivel"
        by_role[str(role)[:60]][level].append(it)

    lines = [
        "# PROPUESTAS DE ACTUALIZACIÓN — whatsthenew",
        f"\nGenerado: {_format_fetch_time()} (respaldo sin IA)",
        f"Total de datos: {len(items)}\n",
        "> Reporte automático de respaldo. Para el análisis con IA usa el agente plan-updater.\n",
    ]

    for role in sorted(by_role):
        lines.append(f"\n## {role}")
        for level in sorted(by_role[role]):
            lines.append(f"\n### Nivel: {level}")
            for it in by_role[role][level][:10]:
                lines.append(
                    f"- **{it.get('title','')}** — {it.get('company','')} · "
                    f"{it.get('location','')} · remoto={it.get('remote')}\n"
                    f"  - Fuente: {it.get('source','')} — {it.get('url','')}\n"
                    f"  - Consultado: {it.get('fetched_at','')} · Publicado: {it.get('posted_at','')}\n"
                    f"  - Skills: {', '.join(it.get('skills', []) or []) or '—'} · "
                    f"Años: {it.get('years', []) or '—'} · Sueldo: {it.get('salary','') or '—'}"
                )
    return "\n".join(lines) + "\n"


def write_report(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
