"""El reporte de respaldo debe ser pequeño, trazable y truncarse con elegancia."""

from __future__ import annotations

from whatsthenew.report import MAX_BYTES, build_fallback_report


def _item(i: int, role: str | None = None, level: str | None = None) -> dict:
    return {
        "title": f"DevOps Engineer {i}",
        "company": f"Company {i}",
        "location": "Remote",
        "remote": True,
        "source": "jobicy",
        "url": f"https://example.com/job/{i}",
        "fetched_at": "17/10/2026 20:00",
        "posted_at": "2026-10-10",
        "skills": ["kubernetes", "terraform"],
        "years": [3, 5],
        "salary": "USD 90k",
        "role": role if role is not None else f"Rol {i % 25}",
        "level": level if level is not None else ["junior", "semi", "senior", "lead"][i % 4],
        "category": "jobs",
    }


def test_reporte_cabe_en_10_kb_y_conserva_trazabilidad() -> None:
    text = build_fallback_report({"items": [_item(i) for i in range(2_000)]})
    assert len(text.encode("utf-8")) <= MAX_BYTES
    assert "Fuente:" in text
    assert "https://example.com/job/" in text
    assert "Consultado:" in text


def test_reporte_se_trunca_con_aviso_si_hay_demasiados_roles() -> None:
    levels = ["junior", "semi", "senior", "lead"]
    items = [
        _item(
            i,
            role=f"Rol {i % 8} con un nombre deliberadamente larguisimo",
            level=levels[(i // 8) % 4],
        )
        for i in range(2_000)
    ]
    text = build_fallback_report({"items": items})
    assert len(text.encode("utf-8")) <= MAX_BYTES
    assert "Reporte truncado" in text


def test_reporte_vacio_no_falla() -> None:
    text = build_fallback_report({"items": []})
    assert "Total de datos: 0" in text
    assert len(text.encode("utf-8")) <= MAX_BYTES
