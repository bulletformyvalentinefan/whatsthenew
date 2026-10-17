"""Carga de configuración (JSON) y variables de entorno.

Regla del proyecto (repositorio público):
- **Secretos y todo lo que "apunta a algo"** (endpoints, URLs base, credenciales,
  user-agent, límites, ritmos) se leen de variables de entorno.
- Los catálogos públicos (roles, fuentes, subreddits) viven en `config/*.json`,
  que NO contienen secretos.

Ningún valor sensible debe quedar escrito en el código.
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

# Valores por defecto NO sensibles (endpoints públicos).
DEFAULT_USER_AGENT = "whatsthenew/0.1 (market watcher)"
DEFAULT_REDDIT_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
DEFAULT_REDDIT_OAUTH_BASE = "https://oauth.reddit.com"
DEFAULT_REDDIT_WWW_BASE = "https://www.reddit.com"
DEFAULT_GITHUB_API_BASE = "https://api.github.com"
# Reddit sin login (espejo público). Trae tema, fecha y nº de respuestas.
DEFAULT_PULLPUSH_URL = (
    "https://api.pullpush.io/reddit/search/submission/"
    "?subreddit={subreddit}&q={query}&size={size}&sort=desc"
)


def _load_json(name: str) -> dict[str, Any]:
    with open(CONFIG_DIR / name, encoding="utf-8") as fh:
        return json.load(fh)


def _env_path(key: str, default: Path) -> Path:
    return Path(os.getenv(key, str(default)))


@dataclass(frozen=True)
class Settings:
    # --- Rutas ---
    plan_file: Path
    output_file: Path
    tmp_raw: Path

    # --- Ritmo / red ---
    http_delay: float
    http_timeout: float
    reddit_delay: float
    reddit_limit: int
    reddit_timeout: float
    reddit_retries: int
    reddit_replies_top_n: int
    user_agent: str

    # --- OpenCode ---
    opencode_bin: str
    opencode_agent: str
    opencode_model: str

    # --- Credenciales Reddit (solo desde .env) ---
    reddit_client_id: str
    reddit_client_secret: str

    # --- Endpoints configurubles (apuntan a algo) ---
    reddit_token_url: str
    reddit_oauth_base: str
    reddit_www_base: str
    pullpush_url: str
    github_api_base: str

    # --- Notificación ---
    discord_webhook: str

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            plan_file=_env_path("PLAN_FILE", ROOT / "GOD_PLAN.md"),
            output_file=_env_path("OUTPUT_FILE", ROOT / "output" / "PROPOSED_UPDATES.md"),
            tmp_raw=_env_path("TMP_RAW", Path("/tmp/whatsthenew_raw.json")),
            http_delay=float(os.getenv("HTTP_DELAY_SECONDS", "4")),
            http_timeout=float(os.getenv("HTTP_TIMEOUT_SECONDS", "25")),
            reddit_delay=float(os.getenv("REDDIT_DELAY_SECONDS", "10")),
            reddit_limit=int(os.getenv("REDDIT_LIMIT", "15")),
            reddit_timeout=float(os.getenv("REDDIT_TIMEOUT_SECONDS", "25")),
            reddit_retries=int(os.getenv("REDDIT_RETRIES", "2")),
            reddit_replies_top_n=int(os.getenv("REDDIT_REPLIES_TOP_N", "5")),
            user_agent=os.getenv("USER_AGENT", DEFAULT_USER_AGENT),
            opencode_bin=os.getenv("OPENCODE_BIN", "opencode"),
            opencode_agent=os.getenv("OPENCODE_AGENT", "plan-updater"),
            opencode_model=os.getenv("OPENCODE_MODEL", ""),
            reddit_client_id=os.getenv("REDDIT_CLIENT_ID", ""),
            reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
            reddit_token_url=os.getenv("REDDIT_TOKEN_URL", DEFAULT_REDDIT_TOKEN_URL),
            reddit_oauth_base=os.getenv("REDDIT_OAUTH_BASE", DEFAULT_REDDIT_OAUTH_BASE),
            reddit_www_base=os.getenv("REDDIT_WWW_BASE", DEFAULT_REDDIT_WWW_BASE),
            pullpush_url=os.getenv("PULLPUSH_URL", DEFAULT_PULLPUSH_URL),
            github_api_base=os.getenv("GITHUB_API_BASE", DEFAULT_GITHUB_API_BASE),
            discord_webhook=os.getenv("DISCORD_WEBHOOK", ""),
        )


def load_sources() -> dict[str, Any]:
    return _load_json("sources.json")


def load_roles() -> dict[str, Any]:
    return _load_json("roles.json")


def load_reddit() -> dict[str, Any]:
    return _load_json("reddit.json")
