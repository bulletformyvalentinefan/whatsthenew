"""Orquestador del pipeline: fetch -> guardar temporal -> analizar -> purgar."""

from __future__ import annotations

import json
import logging

from . import fetchers as F
from .analyze import run_analysis
from .classify import classify  # noqa: F401  (reexport para uso externo)
from .cleanup import purge_tmp
from .config import Settings, load_reddit, load_roles, load_sources
from .models import Item, items_to_payload, now_local_iso
from .report import build_fallback_report, write_report

log = logging.getLogger("whatsthenew")

# Consultas base por rol (para tableros que aceptan palabra clave).
ROLE_QUERIES = ["devops", "cloud engineer", "site reliability", "platform engineer", "backend engineer"]
JOBICY_TAGS = ["devops", "cloud", "sre", "platform", "backend"]
REDDIT_QUERIES = ["hired", "salary", "study plan", "junior remote"]


def _safe(fn, *args, **kwargs) -> list[Item]:
    """Ejecuta un fetcher y aísla sus fallos."""
    try:
        result = fn(*args, **kwargs)
        log.info("OK  %s -> %d items", getattr(fn, "__name__", fn), len(result))
        return result
    except Exception as exc:  # noqa: BLE001
        log.warning("FALLO %s: %s", getattr(fn, "__name__", fn), exc)
        return []


def collect(settings: Settings, client: "F.HttpClient", reddit: "F.RedditClient") -> list[Item]:
    sources = load_sources()
    roles = load_roles()
    F.jobs.STACK = roles["stack"]
    rcfg = load_reddit()
    items: list[Item] = []

    # --- Empleos globales ---
    for s in sources.get("jobs_global", []):
        if not s.get("enabled"):
            continue
        sid = s["id"]
        if sid == "weworkremotely":
            items += _safe(F.fetch_rss_jobs, client, s["url"], "weworkremotely.com")
        elif sid == "seek":
            items += _safe(F.fetch_seek_jobs, client, s["url"], ROLE_QUERIES[:2], 1)
        elif sid == "jobicy":
            items += _safe(F.fetch_jobicy, client, s["url"], JOBICY_TAGS[:3])
        elif sid == "hackernews":
            items += _safe(F.fetch_hackernews_whoishiring, client, s["url"], "who is hiring")
        elif sid in {"remotive", "remoteok", "workingnomads", "himalayas", "landingjobs"}:
            items += _safe(F.fetch_json_board, client, sid, s["url"])

    # --- Empleos Chile ---
    for s in sources.get("jobs_chile", []):
        if not s.get("enabled"):
            continue
        if s["id"] == "getonbrd":
            items += _safe(F.fetch_getonbrd, client, s["url"])
        else:
            log.info("Pendiente parser HTML: %s", s["id"])

    # --- Noticias ---
    for s in sources.get("news", []):
        if s.get("enabled") and s.get("type") == "rss":
            items += _safe(F.fetch_rss, client, s["url"], s["id"], "news")

    # --- Blogs de empresas ---
    for s in sources.get("company_blogs", []):
        if s.get("enabled") and s.get("url"):
            items += _safe(F.fetch_rss, client, s["url"], s["id"], "company_blog")

    # --- Roadmaps ---
    for s in sources.get("roadmaps", []):
        if not s.get("enabled"):
            continue
        if s["id"] == "devto":
            items += _safe(F.fetch_devto, client, s["url"])
        elif s["id"] == "roadmapsh":
            items += _safe(F.fetch_github_repo, client, s["repo"], s.get("branch", "master"))

    # --- Reddit ---
    subs = rcfg["subreddits"]
    for sub in subs["role"][:4]:
        for q in REDDIT_QUERIES[:2]:
            items += _safe(reddit.search, sub, q, "month", "top", 10)

    return items


def run(settings: Settings) -> int:
    sources = load_sources()
    defaults = sources["defaults"]

    with F.HttpClient(settings.user_agent, delay=settings.http_delay) as client:
        reddit = F.RedditClient(
            user_agent=settings.user_agent,
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            delay=settings.reddit_delay,
        )
        items = collect(settings, client, reddit)

    meta = {
        "generated_at": now_local_iso(),
        "count": len(items),
        "roles_file": "config/roles.json",
        "sources_file": "config/sources.json",
        "user_agent": defaults["user_agent"],
    }
    payload = items_to_payload(items, meta)
    settings.tmp_raw.parent.mkdir(parents=True, exist_ok=True)
    settings.tmp_raw.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Datos crudos escritos en %s (%d items)", settings.tmp_raw, len(items))

    # Respaldo determinista SIEMPRE (por si la IA falla).
    write_report(build_fallback_report(payload), settings.output_file)

    # Análisis con IA (sobrescribe el archivo si tiene éxito).
    try:
        result = run_analysis(settings)
        log.info("OpenCode rc=%s ok=%s", result.returncode, result.ok)
    except Exception as exc:  # noqa: BLE001
        log.warning("Análisis IA no disponible (%s). Se deja el respaldo.", exc)

    # Purga de datos efímeros.
    purged = purge_tmp(settings.tmp_raw)
    log.info("Temporal purgado: %s", purged)
    return 0 if purged else 1
