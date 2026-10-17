"""Purga de datos efímeros: libera disco tras el análisis."""

from __future__ import annotations

import contextlib
from pathlib import Path


def purge_tmp(tmp_raw: Path) -> bool:
    """Borra el JSON crudo temporal. Devuelve True si ya no existe."""
    with contextlib.suppress(FileNotFoundError):
        tmp_raw.unlink()
    return not tmp_raw.exists()


def purge_extra(paths: list[Path]) -> list[Path]:
    """Borra rutas extra y devuelve las que quedaron."""
    remaining: list[Path] = []
    for p in paths:
        with contextlib.suppress(FileNotFoundError):
            if p.is_dir():
                import shutil

                shutil.rmtree(p)
            else:
                p.unlink()
        if p.exists():
            remaining.append(p)
    return remaining
