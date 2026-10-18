"""Genera un reporte determinista (respaldo sin IA) agrupando por rol y nivel.

El reporte es un **resumen**, no un volcado: el requisito es que ocupe menos de
10 KB y que cada fila conserve su fuente (dominio + URL) y la fecha de consulta.
El detalle completo vive en el JSON crudo de la corrida.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Límites deliberados: el reporte es para leer, no para archivar.
MAX_BYTES = 9_800
SUMMARY_ROLES = 12
DETAIL_ROLES = 8
ITEMS_PER_LEVEL = 3

TRUNCATED_NOTE = (
    "\n\n---\n\n"
    "_(Reporte truncado para mantenerlo bajo 10 KB. "
    "El detalle completo, con todas las fuentes, está en el JSON crudo de la corrida.)_\n"
)


def _format_fetch_time() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def _role_key(item: dict[str, Any]) -> str:
    role = item.get("role") or item.get("title") or "(sin rol)"
    return str(role)[:60]


def cap_report_text(text: str, limit: int = MAX_BYTES) -> str:
    """Recorta en un salto de línea para no dejar una fila a medias."""
    encoded = text.encode("utf-8")
    if len(encoded) <= limit:
        return text
    cut = encoded[: limit - len(TRUNCATED_NOTE.encode("utf-8"))].decode("utf-8", "ignore")
    cut = cut.rsplit("\n", 1)[0]
    return cut + TRUNCATED_NOTE


def build_fallback_report(payload: dict[str, Any]) -> str:
    items = payload.get("items", [])
    by_role: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))

    for it in items:
        level = it.get("level") or "sin nivel"
        by_role[_role_key(it)][str(level)].append(it)

    ranked = sorted(
        by_role.items(),
        key=lambda kv: (-sum(len(v) for v in kv[1].values()), kv[0]),
    )

    lines = [
        "# PROPUESTAS DE ACTUALIZACIÓN — whatsthenew",
        f"\nGenerado: {_format_fetch_time()} (respaldo sin IA)",
        f"Total de datos: {len(items)} · roles distintos: {len(by_role)}",
        "> Resumen automático de respaldo. El análisis con IA lo produce el agente plan-updater.",
        "",
        "## Resumen por rol",
        "",
        "| Rol | Avisos |",
        "|---|---:|",
    ]
    for role, levels in ranked[:SUMMARY_ROLES]:
        n = sum(len(v) for v in levels.values())
        lines.append(f"| {role} | {n} |")
    if len(ranked) > SUMMARY_ROLES:
        lines.append(f"| … (+{len(ranked) - SUMMARY_ROLES} roles) | |")

    for role, levels in ranked[:DETAIL_ROLES]:
        lines.append(f"\n## {role}")
        for level in sorted(levels):
            lines.append(f"\n### Nivel: {level}")
            for it in levels[level][:ITEMS_PER_LEVEL]:
                lines.append(
                    f"- **{it.get('title', '')}** — {it.get('company', '')} · "
                    f"{it.get('location', '')} · remoto={it.get('remote')}"
                )
                lines.append(
                    f"  - Fuente: {it.get('source', '')} — {it.get('url', '')}"
                )
                lines.append(
                    f"  - Consultado: {it.get('fetched_at', '')} · "
                    f"Publicado: {it.get('posted_at', '')}"
                )
                skills = ", ".join(it.get("skills", []) or []) or "—"
                years = it.get("years", []) or "—"
                salary = it.get("salary", "") or "—"
                lines.append(f"  - Skills: {skills} · Años: {years} · Sueldo: {salary}")
                if it.get("category") == "reddit":
                    replies = it.get("replies", 0) or 0
                    lines.append(
                        f"  - Respuestas: {replies}"
                        f"{' (sí)' if it.get('has_replies') else ' (no)'}"
                    )

    return cap_report_text("\n".join(lines) + "\n")


def write_report(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
