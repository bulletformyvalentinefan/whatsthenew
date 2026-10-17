"""Carga de configuración (JSON) y variables de entorno.

Centraliza rutas, ritmo de peticiones y catálogos (fuentes, roles, Reddit).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # python-dotenv es opcional
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"


def _load_json(name: str) -> dict[str, Any]:
    with open(CONFIG_DIR / name, encoding="utf-8") as fh:
        return json.load(fh)


@dataclass(frozen=True)
class Settings:
    plan_file: Path
    output_file: Path
    tmp_raw: Path
    http_delay: float
    reddit_delay: float
    user_agent: str
    opencode_bin: str
    opencode_agent: str
    opencode_model: str
    reddit_client_id: str
    reddit_client_secret: str
    discord_webhook: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            plan_file=Path(os.getenv("PLAN_FILE", ROOT / "GOD_PLAN.md")),
            output_file=Path(os.getenv("OUTPUT_FILE", ROOT / "output" / "PROPOSED_UPDATES.md")),
            tmp_raw=Path(os.getenv("TMP_RAW", "/tmp/whatsthenew_raw.json")),
            http_delay=float(os.getenv("HTTP_DELAY_SECONDS", "4")),
            reddit_delay=float(os.getenv("REDDIT_DELAY_SECONDS", "10")),
            user_agent=os.getenv(
                "USER_AGENT",
                "whatsthenew/0.1 (+https://github.com/bulletformyvalentinefan/whatsthenew)",
            ),
            opencode_bin=os.getenv("OPENCODE_BIN", "opencode"),
            opencode_agent=os.getenv("OPENCODE_AGENT", "plan-updater"),
            opencode_model=os.getenv("OPENCODE_MODEL", ""),
            reddit_client_id=os.getenv("REDDIT_CLIENT_ID", ""),
            reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
            discord_webhook=os.getenv("DISCORD_WEBHOOK", ""),
        )


def load_sources() -> dict[str, Any]:
    return _load_json("sources.json")


def load_roles() -> dict[str, Any]:
    return _load_json("roles.json")


def load_reddit() -> dict[str, Any]:
    return _load_json("reddit.json")
