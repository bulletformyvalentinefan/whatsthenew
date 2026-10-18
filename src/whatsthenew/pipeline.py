"""Orquestador del pipeline: fetch -> guardar temporal -> analizar -> purgar."""

from __future__ import annotations

import json
import logging
from typing import Any

from . import fetchers as F
from .analyze import run_analysis
from .classify import classify  # noqa: F401  (reexport para uso externo)
from .cleanup import purge_extra, purge_tmp
from .config import Settings, load_reddit, load_roles, load_sources
from .models import Item, items_to_payload, now_local_iso
from .publish import ensure_plan_clone, push_proposal
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


def enrich_reddit_replies(reddit: F.RedditClient, items: list[Item], top_n: int) -> None:
    """Consulta el nº de respuestas de los top N hilos por (subreddit, consulta).

    Es 1 petición extra por hilo; se limita a los primeros N de cada búsqueda
    para no disparar el nº de llamadas. Corre semanal: tardar no importa.
    """
    if top_n <= 0:
        return
    seen: dict[tuple[str, str], int] = {}
    for it in items:
        key = (it.source, it.query)
        if seen.get(key, 0) >= top_n:
            continue
        seen[key] = seen.get(key, 0) + 1
        try:
            it.replies, it.has_replies = reddit.thread_replies(it.url)
        except Exception as exc:  # noqa: BLE001
            log.warning("Reddit respuestas (%s): %s", it.url, exc)


def collect_reddit(
    settings: Settings, reddit: F.RedditClient, client: F.HttpClient, rcfg: dict[str, Any]
) -> list[Item]:
    """Reddit sin login.

    1) **PullPush** (espejo público): en 1 petición da tema, fecha y nº de
       respuestas. Es el camino principal.
    2) **RSS de Reddit** de respaldo (con conteo de respuestas por hilo) para
       cuando PullPush no devuelve nada.
    """
    subs = rcfg["subreddits"]["role"][:4]
    queries = REDDIT_QUERIES[:2]

    if settings.pullpush_url:
        pull: list[Item] = []
        for sub in subs:
            for q in queries:
                pull += _safe(
                    F.fetch_pullpush, client, settings.pullpush_url, sub, q, settings.reddit_limit
                )
        if pull:
            log.info("Reddit: %d items vía PullPush (sin login).", len(pull))
            return pull
        log.warning("Reddit: PullPush sin resultados; se prueba el RSS de Reddit.")

    # Respaldo: RSS de Reddit + conteo de respuestas (login OAuth opcional).
    if reddit.authenticate():
        log.info("Reddit: autenticado por OAuth.")
    else:
        log.info("Reddit: modo RSS (sin credenciales), pausa de %.0f s.", reddit.delay)

    rss_items: list[Item] = []
    for sub in subs:
        for q in queries:
            rss_items += _safe(reddit.search, sub, q, "month", "top")

    enrich_reddit_replies(reddit, rss_items, settings.reddit_replies_top_n)
    return rss_items


def collect(settings: Settings, client: F.HttpClient, reddit: F.RedditClient) -> list[Item]:
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
            items += _safe(F.fetch_seek_jobs, client, s["url"], ROLE_QUERIES[:2], 1, s.get("web_base", ""))
        elif sid == "jobicy":
            items += _safe(F.fetch_jobicy, client, s["url"], JOBICY_TAGS[:3])
        elif sid == "hackernews":
            items += _safe(F.fetch_hackernews_whoishiring, client, s["url"], "who is hiring", s.get("web_base", ""))
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
            items += _safe(F.fetch_github_repo, client, s["repo"], s.get("branch", "master"), settings.github_api_base)

    # --- Reddit (sin login; desactivado por defecto porque bloquea por IP) ---
    if settings.enable_reddit:
        items += collect_reddit(settings, reddit, client, rcfg)
    else:
        log.info("Reddit desactivado (ENABLE_REDDIT=0): se usan solo fuentes web.")

    return items


def run(settings: Settings) -> int:
    with F.HttpClient(
        settings.user_agent, delay=settings.http_delay, timeout=settings.http_timeout
    ) as client:
        reddit = F.RedditClient(
            user_agent=settings.user_agent,
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            delay=settings.reddit_delay,
            limit=settings.reddit_limit,
            timeout=settings.reddit_timeout,
            retries=settings.reddit_retries,
            token_url=settings.reddit_token_url,
            oauth_base=settings.reddit_oauth_base,
            www_base=settings.reddit_www_base,
        )
        items = collect(settings, client, reddit)

    meta = {
        "generated_at": now_local_iso(),
        "count": len(items),
        "roles_file": "config/roles.json",
        "sources_file": "config/sources.json",
        "user_agent": settings.user_agent,
        "reddit_auth": "oauth" if reddit.has_credentials else "rss",
    }
    payload = items_to_payload(items, meta)
    settings.tmp_raw.parent.mkdir(parents=True, exist_ok=True)
    settings.tmp_raw.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Datos crudos escritos en %s (%d items)", settings.tmp_raw, len(items))

    # Respaldo determinista SIEMPRE (por si la IA falla).
    write_report(build_fallback_report(payload), settings.output_file)

    # Plan de carrera: si vamos a publicar, se clona el repositorio PRIVADO del plan.
    # El clon es efímero: vive en PLAN_DIR y se borra al terminar.
    plan_path = settings.plan_file
    if settings.publish_proposal:
        try:
            plan_path = ensure_plan_clone(settings)
            log.info("Repo del plan listo en %s", plan_path)
        except Exception as exc:  # noqa: BLE001
            log.warning("No se pudo clonar el repo del plan (%s); uso %s", exc, plan_path)

    # Análisis con IA (sobrescribe el reporte si tiene éxito y escribe el plan propuesto).
    try:
        result = run_analysis(settings, plan_path)
        log.info("OpenCode rc=%s ok=%s", result.returncode, result.ok)
    except Exception as exc:  # noqa: BLE001
        log.warning("Análisis IA no disponible (%s). Se deja el respaldo.", exc)

    # Publicar la propuesta como PR en el repo privado (nunca fusiona solo).
    if settings.publish_proposal:
        proposed = settings.proposed_plan_file
        if proposed.exists():
            report_text = settings.output_file.read_text(encoding="utf-8")
            res = push_proposal(settings, proposed.read_text(encoding="utf-8"), report_text, len(items))
            log.info("Propuesta: ok=%s rama=%s %s", res.ok, res.branch, res.detail)
        else:
            log.warning("Sin plan propuesto (%s): no se abre PR.", proposed)

    # Purga de datos efímeros (JSON crudo y clon del plan).
    purged = purge_tmp(settings.tmp_raw)
    if settings.publish_proposal:
        remaining = purge_extra([settings.plan_dir])
        purged = purged and not remaining
    log.info("Temporal purgado: %s", purged)
    return 0 if purged else 1
