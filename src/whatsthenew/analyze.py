"""Puente hacia OpenCode: el motor que ordena y compara los datos.

Se invoca la CLI en modo no interactivo:

    opencode run --agent plan-updater --auto --file /tmp/whatsthenew_raw.json "<instrucción>"

El agente `plan-updater` (definido en .opencode/agents/plan-updater.md) lee el JSON
crudo y el GOD_PLAN.md, y escribe el reporte en output/PROPOSED_UPDATES.md.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import Settings

PROMPT = """Tienes dos archivos:
1. El JSON crudo del mercado (adjunto): {raw}
2. El plan de carrera actual: {plan}

Tarea:
- Clasifica por rol y por NIVEL (junior/semi/senior/lead). NO excluyas nada.
- Para cada rol y nivel, resume qué pide el mercado: años, stack, sueldos, ubicación, remoto.
- Marca el DELTA entre lo que pide un senior y un junior del mismo rol.
- Compara con lo que ya dice el plan y propone cambios concretos.
- Cada fila DEBE citar su fuente (dominio + URL) y la fecha de consulta (dd/mm/aaaa hh:mm).

Escribe el resultado SOLO en el archivo: {output}
Formato: Markdown. Máximo 2 páginas.
"""


@dataclass
class AnalyzeResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    output_file: Path


def run_analysis(settings: Settings) -> AnalyzeResult:
    if shutil.which(settings.opencode_bin) is None:
        raise FileNotFoundError(
            f"No encontré el binario '{settings.opencode_bin}'. Instala OpenCode o ajusta OPENCODE_BIN."
        )

    prompt = PROMPT.format(
        raw=settings.tmp_raw,
        plan=settings.plan_file,
        output=settings.output_file,
    )

    cmd = [
        settings.opencode_bin, "run",
        "--agent", settings.opencode_agent,
        "--auto",
        "--file", str(settings.tmp_raw),
    ]
    if settings.opencode_model:
        cmd += ["--model", settings.opencode_model]
    cmd.append(prompt)

    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(settings.plan_file.parent))
    return AnalyzeResult(
        ok=proc.returncode == 0 and settings.output_file.exists(),
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        output_file=settings.output_file,
    )
