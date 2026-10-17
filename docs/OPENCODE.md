# Integración con OpenCode — whatsthenew

OpenCode es el **motor de análisis**: recibe el JSON crudo del mercado y el `GOD_PLAN.md`, y produce
el reporte de propuestas.

## Cómo se invoca

`analyze.py` ejecuta la CLI en modo no interactivo:

```bash
opencode run \
  --agent plan-updater \
  --auto \
  --file /tmp/whatsthenew_raw.json \
  "Lee el JSON adjunto y GOD_PLAN.md, clasifica por rol y nivel, y escribe output/PROPOSED_UPDATES.md"
```

Flags usados:

| Flag | Para qué |
|---|---|
| `--agent plan-updater` | Usa el agente definido en `.opencode/agents/plan-updater.md` |
| `--auto` | Aprueba permisos no denegados (para que escriba el reporte sin interacción) |
| `--file` | Adjunta el JSON crudo al mensaje |
| `--model` | (Opcional) `provider/model#variant` para forzar un modelo |

## Archivos de configuración

- `opencode.jsonc` — configuración del proyecto (agente por defecto, permisos).
- `.opencode/agents/plan-updater.md` — el agente que ordena los datos.
- `.opencode/commands/update-plan.md` — comando `/update-plan` para lanzarlo desde la TUI.

## Permisos del agente

`plan-updater` puede:
- **leer** todo el repo y `/tmp`,
- **escribir** solo dentro de `output/`,
- **ejecutar shell** solo para `git status`/`git diff` (no push).

Así el análisis nunca toca el resto del proyecto ni hace `push`.

## Flujo manual (TUI)

1. Ejecuta el fetch: `python -m whatsthenew run` (deja el JSON temporal si falla la IA).
2. O dentro de OpenCode: `/update-plan`.
3. Revisa `output/PROPOSED_UPDATES.md` y decide qué se aplica al plan.

## Portabilidad

El prompt vive en `analyze.py` (`PROMPT`). Si prefieres usar otro motor (API de Gemini, etc.), basta
reemplazar `run_analysis()` conservando la misma entrada (JSON + plan) y salida (Markdown trazable).
