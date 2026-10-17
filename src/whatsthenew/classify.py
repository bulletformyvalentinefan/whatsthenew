"""Clasificación de cada dato: rol, nivel, años y stack.

Regla del proyecto: NO se excluye ningún rol ni nivel. Aquí solo se etiqueta.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

_LEVEL_PATTERNS: list[tuple[str, str]] = [
    ("principal", r"\bprincipal\b"),
    ("staff", r"\bstaff\b"),
    ("lead", r"\b(lead|tech lead|team lead|jefe)\b"),
    ("semi", r"\b(semi[- ]?senior|ssr|mid[- ]?level|intermediate|ii|semi)\b"),
    ("senior", r"\b(senior|sr\.?|iii)\b"),
    ("junior", r"\b(junior|jr\.?|entry[- ]?level|trainee|intern|becario|sin experiencia)\b"),
]

_YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|años?|yrs?)", re.IGNORECASE)
_REMOTE_RE = re.compile(r"\b(remote|remoto|teletrabajo|home office|hybrid|híbrido)\b", re.IGNORECASE)


def detect_level(title: str, text: str = "") -> str:
    """Devuelve junior|semi|senior|lead|staff|principal o '' si no se detecta."""
    haystack = f"{title} {text}".lower()
    for level, pattern in _LEVEL_PATTERNS:
        if re.search(pattern, haystack, re.IGNORECASE):
            return level
    return ""


def extract_years(text: str) -> list[int]:
    """Extrae los años de experiencia mencionados (ej: '5+ años' -> [5])."""
    return sorted({int(m.group(1)) for m in _YEARS_RE.finditer(text or "")})


def extract_skills(text: str, stack: Iterable[str]) -> list[str]:
    """Devuelve el stack presente en el texto (match por palabra)."""
    low = (text or "").lower()
    found: list[str] = []
    for tech in stack:
        if re.search(rf"(?<![a-z0-9]){re.escape(tech.lower())}(?![a-z0-9])", low):
            found.append(tech)
    return found


def detect_remote(location: str, text: str = "") -> bool | None:
    haystack = f"{location} {text}"
    if re.search(r"\b(hybrid|híbrido|presencial|on-?site)\b", haystack, re.IGNORECASE):
        return False
    if _REMOTE_RE.search(haystack):
        return True
    return None


def classify(title: str, text: str, stack: Iterable[str], location: str = "") -> dict:
    """Etiqueta un dato. Punto único usado por todos los fetchers."""
    return {
        "level": detect_level(title, text),
        "years": extract_years(text),
        "skills": extract_skills(f"{title} {text}", stack),
        "remote": detect_remote(location, text),
    }
