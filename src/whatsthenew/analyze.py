"""Puente hacia OpenCode: el motor que ordena y compara los datos.

Se invoca la CLI en modo no interactivo:

    opencode run --agent plan-updater --auto --file /tmp/whatsthenew_raw.json "<instrucción>"

El agente `plan-updater` (definido en .opencode/agents/plan-updater.md) lee el JSON
crudo y el GOD_PLAN.md, y escribe DOS salidas dentro de `output/`:

- `output/PROPOSED_UPDATES.md`  -> propuestas razonadas (fuente + fecha).
- `output/GOD_PLAN.proposed.md` -> el plan completo con los cambios ya aplicados,
  listo para convertirse en PR.

El proceso SIEMPRE corre con `cwd = raíz del repositorio` para que OpenCode
descubra `.opencode/agents/`. El plan puede vivir fuera (p. ej. un clon del repo
privado): se pasa su ruta absoluta en el prompt.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import ROOT, Settings
from .report import cap_report_text

PROMPT = """Tienes el JSON crudo del mercado adjunto ({raw}) y el plan de carrera actual en {plan}.

Tarea:
- Clasifica por rol y por NIVEL (junior/semi/senior/lead). NO excluyas nada.
- Para cada rol y nivel, resume qué pide el mercado: años, stack, sueldos, ubicación, remoto.
- Marca el DELTA entre lo que pide un senior y un junior del mismo rol.
- Compara con lo que ya dice el plan y propone cambios concretos.
- Cada fila DEBE citar su fuente (dominio + URL) y la fecha de consulta (dd/mm/aaaa hh:mm).

Escribe DOS archivos:

1. {output} -> el reporte de propuestas (Markdown, máximo 2 páginas).
2. {proposed} -> el plan de carrera COMPLETO ya actualizado con esos cambios.
   Conserva la estructura y el estilo del plan original; si algo no cambia, déjalo igual.
   No inventes secciones nuevas que no aporten datos del mercado.
"""


@dataclass
class AnalyzeResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    output_file: Path
    proposed_plan_file: Path


def run_analysis(settings: Settings, plan_path: Path) -> AnalyzeResult:
    if shutil.which(settings.opencode_bin) is None:
        raise FileNotFoundError(
            f"No encontré el binario '{settings.opencode_bin}'. Instala OpenCode o ajusta OPENCODE_BIN."
        )

    settings.output_file.parent.mkdir(parents=True, exist_ok=True)
    settings.proposed_plan_file.parent.mkdir(parents=True, exist_ok=True)

    prompt = PROMPT.format(
        raw=settings.tmp_raw,
        plan=plan_path,
        output=settings.output_file,
        proposed=settings.proposed_plan_file,
    )

    cmd = [
        settings.opencode_bin, "run",
        "--agent", settings.opencode_agent,
        "--auto",
        "--standalone",
        "--file", str(settings.tmp_raw),
    ]
    if settings.opencode_model:
        cmd += ["--model", settings.opencode_model]
    cmd.append(prompt)

    # cwd = raíz del repo: así OpenCode encuentra `.opencode/agents/plan-updater.md`
    # aunque el plan viva en otro sitio (clon del repo privado).
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    ok = proc.returncode == 0 and settings.output_file.exists()

    # Requisito del proyecto: el reporte pesa menos de 10 KB. La IA no siempre
    # lo respeta, así que se recorta de forma determinista.
    if ok:
        text = settings.output_file.read_text(encoding="utf-8")
        capped = cap_report_text(text)
        if capped != text:
            settings.output_file.write_text(capped, encoding="utf-8")

    return AnalyzeResult(
        ok=ok,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        output_file=settings.output_file,
        proposed_plan_file=settings.proposed_plan_file,
    )
