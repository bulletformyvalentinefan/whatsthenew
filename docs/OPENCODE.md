# Integración con OpenCode — whatsthenew

OpenCode es el **motor de análisis**: recibe el JSON crudo del mercado y el `GOD_PLAN.md`,
y produce **dos** salidas: el reporte de propuestas y el plan completo ya actualizado.

## Cómo se invoca

`analyze.py` ejecuta la CLI en modo no interactivo:

```bash
opencode run \
  --agent plan-updater \
  --auto \
  --standalone \
  --file /tmp/whatsthenew_raw.json \
  "Lee el JSON adjunto y GOD_PLAN.md, clasifica por rol y nivel, y escribe \
   output/PROPOSED_UPDATES.md y output/GOD_PLAN.proposed.md"
```

Siempre con `cwd = raíz del repositorio`, para que OpenCode descubra
`.opencode/agents/plan-updater.md` **aunque el plan viva fuera** (p. ej. un clon del
repositorio privado en `/tmp`).

Flags usados:

| Flag | Para qué |
|---|---|
| `--agent plan-updater` | Usa el agente definido en `.opencode/agents/plan-updater.md` |
| `--auto` | Aprueba permisos no denegados (escribe sin interacción) |
| `--standalone` | Arranca un servidor privado y efímero (mejor para cron) |
| `--file` | Adjunta el JSON crudo al mensaje |
| `--model` | (Opcional) `provider/model#variant` para forzar un modelo |

## Proveedor del modelo

La inferencia corre en el **proveedor** (nada de cómputo pesado en tu servidor). Solo
necesita una clave, que va **en el `.env`**, nunca en el repo:

```bash
OPENCODE_MODEL=openrouter/deepseek/deepseek-v4.1-flash:decart
OPENROUTER_API_KEY=...
```

## Salidas

| Archivo | Qué es |
|---|---|
| `output/PROPOSED_UPDATES.md` | El reporte razonado (fuente + fecha). Es lo que lees. |
| `output/GOD_PLAN.proposed.md` | El plan completo con los cambios aplicados. Es lo que se convierte en PR. |

## Archivos de configuración

- `opencode.jsonc` — configuración del proyecto (agente por defecto, permisos).
- `.opencode/agents/plan-updater.md` — el agente que ordena los datos.
- `.opencode/commands/update-plan.md` — comando `/update-plan` para lanzarlo desde la TUI.

## Permisos del agente

`plan-updater` puede:
- **leer** todo el repo y `/tmp`,
- **escribir** solo dentro de `output/`,
- **ejecutar shell** solo para `git status`/`git diff` (no push).

Así el análisis nunca toca el resto del proyecto ni hace `push`. El PR lo abre
`publish.py` (Python), no la IA.

## Flujo manual (TUI)

1. Ejecuta el fetch: `python -m whatsthenew run` (deja el JSON temporal si falla la IA).
2. O dentro de OpenCode: `/update-plan`.
3. Revisa `output/PROPOSED_UPDATES.md` y el plan propuesto.

## Portabilidad

El prompt vive en `analyze.py` (`PROMPT`). Si prefieres usar otro motor (API de Gemini,
etc.), basta reemplazar `run_analysis()` conservando la misma entrada (JSON + plan) y
salida (reporte + plan propuesto trazables).
