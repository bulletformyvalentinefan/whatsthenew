"""Publica la propuesta del plan como Pull Request en el repositorio PRIVADO.

Flujo (contenedor efímero, sin login interactivo):

1. Clona (o actualiza) el repositorio privado del plan en `PLAN_DIR`.
2. Crea una rama semanal `proposal/AAAA-Wss`.
3. Sustituye `GOD_PLAN.md` por el plan propuesto por la IA y añade el reporte
   en `proposals/AAAA-Wss.md` (así el PR muestra el "por qué", no solo el diff).
4. Hace commit, push y abre el PR contra la rama principal.

El merge lo decide una persona: el pipeline nunca fusiona ni toca `main`.
Regla del proyecto: **propone, no impone**.
"""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx

from .config import Settings

log = logging.getLogger("whatsthenew")

PLAN_FILENAME = "GOD_PLAN.md"
PROPOSALS_DIRNAME = "proposals"
# Un plan real ocupa bastante más que esto; evita abrir un PR que "borre" el plan
# si la IA devolvió una salida vacía o truncada.
MIN_PLAN_CHARS = 200


@dataclass
class PublishResult:
    ok: bool
    branch: str = ""
    pr_url: str = ""
    detail: str = ""


# ---------------------------------------------------------------------------
# Utilidades puras (fáciles de probar)
# ---------------------------------------------------------------------------
def iso_week_branch(prefix: str, now: datetime | None = None) -> str:
    """Rama de la semana ISO, p. ej. `proposal/2026-W02`."""
    now = now or datetime.now(UTC)
    year, week, _ = now.isocalendar()
    return f"{prefix}/{year}-W{week:02d}"


def proposal_file_name(branch: str) -> str:
    """Nombre del archivo de propuestas dentro del repo del plan."""
    return f"{branch.replace('/', '-')}.md"


def is_plausible_plan(text: str) -> bool:
    """Evita sustituir el plan por una salida vacía o truncada."""
    return len(text.strip()) >= MIN_PLAN_CHARS


def redact(text: str, token: str) -> str:
    """Quita el token de cualquier mensaje antes de registrarlo."""
    if token:
        text = text.replace(token, "***")
    return text


def render_pr_body(branch: str, count: int, generated_at: str, report_relpath: str) -> str:
    """Cuerpo del PR: contexto para revisar sin abrir el diff entero."""
    return "\n".join(
        [
            "## Propuesta semanal de actualización del plan",
            "",
            f"- **Semana:** `{branch}`",
            f"- **Datos de mercado analizados:** {count}",
            f"- **Generado:** {generated_at}",
            "",
            "Este PR sustituye `GOD_PLAN.md` por la versión propuesta por la IA a partir del",
            "mercado de la semana. El motivo de cada cambio está en el reporte adjunto",
            f"([`{report_relpath}`](../blob/{branch}/{report_relpath})).",
            "",
            "> Revisa el diff y fusiona solo si estás de acuerdo. Cerrar el PR no cambia nada.",
            "",
            "_Generado automáticamente por whatsthenew._",
        ]
    )


# ---------------------------------------------------------------------------
# Git (subprocess)
# ---------------------------------------------------------------------------
def _auth_url(settings: Settings) -> str:
    tok = settings.plan_repo_token
    return f"https://x-access-token:{tok}@github.com/{settings.plan_repo}.git"


def _clean_url(settings: Settings) -> str:
    return f"{settings.github_web}/{settings.plan_repo}.git"


def _git(settings: Settings, args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args[:2])} falló: {redact(proc.stderr.strip(), settings.plan_repo_token)}"
        )
    return proc


def ensure_plan_clone(settings: Settings) -> Path:
    """Clona o actualiza el repo del plan. Devuelve la ruta de `GOD_PLAN.md`."""
    dest = settings.plan_dir
    if not (dest / ".git").is_dir():
        dest.parent.mkdir(parents=True, exist_ok=True)
        _git(settings, ["clone", _auth_url(settings), str(dest)], cwd=dest.parent)
    # En ambos casos dejamos el remoto sin token, traemos y nos situamos en la rama.
    _git(settings, ["remote", "set-url", "origin", _clean_url(settings)], cwd=dest)
    _git(settings, ["fetch", "--prune", "origin"], cwd=dest)
    _git(
        settings,
        ["checkout", "-B", settings.plan_repo_branch, f"origin/{settings.plan_repo_branch}"],
        cwd=dest,
    )
    return dest / PLAN_FILENAME


def _commit_and_push(settings: Settings, branch: str, message: str) -> bool:
    """Crea la rama, hace commit y push. Devuelve False si no había cambios."""
    dest = settings.plan_dir
    _git(settings, ["checkout", "-B", branch], cwd=dest)
    status = _git(settings, ["status", "--porcelain"], cwd=dest).stdout.strip()
    if not status:
        return False
    _git(settings, ["add", "-A"], cwd=dest)
    _git(
        settings,
        [
            "-c", f"user.name={settings.git_author_name}",
            "-c", f"user.email={settings.git_author_email}",
            "commit", "-m", message,
        ],
        cwd=dest,
    )
    _git(settings, ["remote", "set-url", "origin", _auth_url(settings)], cwd=dest)
    try:
        _git(settings, ["push", "--force", "--set-upstream", "origin", branch], cwd=dest)
    finally:
        _git(settings, ["remote", "set-url", "origin", _clean_url(settings)], cwd=dest)
    return True


# ---------------------------------------------------------------------------
# GitHub API (crear el PR)
# ---------------------------------------------------------------------------
def _open_pr(settings: Settings, branch: str, title: str, body: str) -> str:
    api = f"{settings.github_api_base}/repos/{settings.plan_repo}/pulls"
    headers = {
        "Authorization": f"Bearer {settings.plan_repo_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"title": title, "head": branch, "base": settings.plan_repo_branch, "body": body}
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(api, headers=headers, json=payload)
        if resp.status_code == 201:
            return resp.json().get("html_url", "")
        if resp.status_code == 422:
            # El PR ya existe (misma semana): devolvemos el que está abierto.
            owner = settings.plan_repo.split("/")[0]
            existing = client.get(
                api,
                headers=headers,
                params={"state": "open", "head": f"{owner}:{branch}"},
            )
            if existing.status_code == 200 and existing.json():
                return existing.json()[0].get("html_url", "")
        raise RuntimeError(
            f"GitHub rechazó el PR ({resp.status_code}): "
            f"{redact(resp.text.strip()[:300], settings.plan_repo_token)}"
        )


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------
def would_publish(settings: Settings) -> bool:
    return settings.publish_proposal


def push_proposal(settings: Settings, proposed_plan: str, report_text: str, count: int) -> PublishResult:
    """Abre el PR con el plan propuesto. Nunca lanza: devuelve el resultado."""
    branch = iso_week_branch(settings.proposal_branch_prefix)

    if not settings.plan_repo or not settings.plan_repo_token:
        return PublishResult(False, branch, detail="PLAN_REPO/PLAN_REPO_TOKEN no configurados.")
    if not is_plausible_plan(proposed_plan):
        return PublishResult(False, branch, detail="El plan propuesto está vacío o truncado; no se abre PR.")

    try:
        plan_path = ensure_plan_clone(settings)
        plan_path.write_text(proposed_plan, encoding="utf-8")

        proposals = settings.plan_dir / PROPOSALS_DIRNAME
        proposals.mkdir(parents=True, exist_ok=True)
        report_relpath = f"{PROPOSALS_DIRNAME}/{proposal_file_name(branch)}"
        (settings.plan_dir / report_relpath).write_text(report_text, encoding="utf-8")

        generated_at = datetime.now(UTC).astimezone().strftime("%d/%m/%Y %H:%M")
        message = f"propuesta(plan): {branch}"
        if not _commit_and_push(settings, branch, message):
            return PublishResult(False, branch, detail="Sin cambios respecto al plan actual.")

        body = render_pr_body(branch, count, generated_at, report_relpath)
        pr_url = _open_pr(settings, branch, f"Propuesta de plan {branch}", body)
        log.info("PR de propuesta abierto: %s", pr_url)
        return PublishResult(True, branch, pr_url=pr_url, detail="PR abierto.")
    except Exception as exc:  # noqa: BLE001
        detail = redact(str(exc), settings.plan_repo_token)
        log.warning("No se pudo publicar la propuesta: %s", detail)
        return PublishResult(False, branch, detail=detail)
