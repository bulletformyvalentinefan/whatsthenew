# Arquitectura — whatsthenew

## Objetivo

Vigilar el mercado tech para los roles del plan de carrera, clasificar la información por rol y
nivel, y generar un reporte de propuestas **sin acumular basura** en un servidor de recursos
acotados.

## Flujo

```text
1. FETCH       fetchers/  -> trae JSON/RSS/HTML de cada fuente (con pausas de 4 s)
2. CLASIFICAR  classify.py -> rol, nivel, años, stack, remoto
3. TEMPORAL    /tmp/whatsthenew_raw.json  (solo en disco volátil)
4. ANÁLISIS    analyze.py -> `opencode run --agent plan-updater` compara con GOD_PLAN.md
5. ENTREGA     output/PROPOSED_UPDATES.md  (< 10 KB)
6. PURGA       cleanup.py -> borra el JSON crudo
```

## Componentes

| Módulo | Rol |
|---|---|
| `fetchers/base.py` | Cliente HTTP con pausa anti-bloqueo |
| `fetchers/jobs.py` | Empleos: GetOnBrd, Seek, Jobicy, tableros JSON, HN, RSS |
| `fetchers/news.py` | Noticias y blogs por RSS |
| `fetchers/reddit.py` | Reddit por OAuth (recomendado) o RSS |
| `fetchers/roadmaps.py` | roadmap.sh (GitHub), dev.to |
| `classify.py` | Etiquetado de nivel/años/stack |
| `analyze.py` | Puente a OpenCode |
| `report.py` | Reporte determinista de respaldo |
| `pipeline.py` | Orquesta las 6 fases |
| `cleanup.py` | Purga de temporales |

## Uso de recursos

- **RAM en espera:** 0 MB (contenedor efímero; ver `docs/../scripts/cron.example`).
- **Disco:** solo el JSON temporal en `/tmp` durante la corrida; se borra al final.
- **Red:** pausas de 4 s (10 s en Reddit) para no gatillar bloqueos.

## Por qué efímero

El plan nace de un servidor con ~3.6 GB de RAM. Dejar un contenedor "durmiendo" consume recursos
inútilmente. El cron del host enciende el contenedor cada 3 días, hace el trabajo y lo apaga.

## Manejo de fallos

Cada fuente se ejecuta dentro de `_safe()`: si una falla (403/429/timeout), se registra y **no
rompe** la corrida. El reporte determinista (`report.py`) se escribe siempre, y el análisis con IA
solo lo mejora si tiene éxito.
