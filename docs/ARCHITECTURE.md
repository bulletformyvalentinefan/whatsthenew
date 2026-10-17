# Arquitectura — whatsthenew

## Objetivo

Vigilar el mercado tech para los roles del plan de carrera, clasificar la información
por rol y nivel, y generar una **propuesta de actualización del plan** —sin acumular
basura en disco ni RAM en un servidor de recursos acotados.

## Flujo

```text
1. FETCH       fetchers/  -> trae JSON/RSS/HTML de cada fuente (con pausas de 4 s)
2. CLASIFICAR  classify.py -> rol, nivel, años, stack, remoto
3. TEMPORAL    /tmp/whatsthenew_raw.json  (solo en disco volátil)
4. PLAN        publish.ensure_plan_clone() -> clona el repo PRIVADO del plan en /tmp
5. ANÁLISIS    analyze.py -> `opencode run --agent plan-updater` compara con GOD_PLAN.md
                            y escribe output/PROPOSED_UPDATES.md + output/GOD_PLAN.proposed.md
6. ENTREGA     report.py -> output/PROPOSED_UPDATES.md  (< 10 KB, respaldo determinista)
7. PROPUESTA   publish.push_proposal() -> rama + PR en el repo privado (no fusiona)
8. PURGA       cleanup.py -> borra el JSON crudo y el clon temporal
```

## Componentes

| Módulo | Rol |
|---|---|
| `fetchers/base.py` | Cliente HTTP con pausa anti-bloqueo y reintentos |
| `fetchers/jobs.py` | Empleos: GetOnBrd, Seek, Jobicy, tableros JSON, HN, RSS |
| `fetchers/news.py` | Noticias y blogs por RSS |
| `fetchers/reddit.py` | Reddit por OAuth (opcional) o RSS |
| `fetchers/pullpush.py` | Reddit sin login (espejo público), con respuestas |
| `fetchers/roadmaps.py` | roadmap.sh (GitHub), dev.to |
| `classify.py` | Etiquetado de nivel/años/stack |
| `analyze.py` | Puente a OpenCode (reporte + plan propuesto) |
| `publish.py` | Clona el repo privado del plan y abre el PR de propuesta |
| `report.py` | Reporte determinista de respaldo |
| `pipeline.py` | Orquesta las fases |
| `cleanup.py` | Purga de temporales (JSON y clon del plan) |

## Separación público / privado

- **Este repositorio (público):** solo código y catálogos. Ningún secreto.
- **Repositorio privado `god-plan`:** el `GOD_PLAN.md` y el histórico de propuestas.
- **Enlace:** el pipeline clona el privado en `/tmp` (efímero), propone cambios y
  abre un PR. Una persona revisa y fusiona. Ver [`PLAN-REPO.md`](PLAN-REPO.md).

## Uso de recursos

- **RAM en espera:** 0 MB (contenedor efímero; ver [`DEPLOY.md`](DEPLOY.md)).
- **RAM durante la corrida:** ~200–500 MB. La inferencia del modelo corre **fuera**,
  en el proveedor: el servidor solo manda el prompt y recibe el texto.
- **Disco:** JSON temporal + clon del plan en `/tmp`; ambos se borran al final.
- **Red:** pausas de 4 s (10 s en Reddit) para no gatillar bloqueos.

## Por qué efímero

Dejar un contenedor "durmiendo" consume recursos inútilmente. El timer del host
enciende el contenedor cada semana, hace el trabajo y lo apaga. Entre ejecuciones no
queda nada encendido, ni el plan en disco.

## Manejo de fallos

Cada fuente se ejecuta dentro de `_safe()`: si una falla (403/429/timeout), se registra
y **no rompe** la corrida. El reporte determinista (`report.py`) se escribe siempre, y
el análisis con IA solo lo mejora si tiene éxito. Si no hay plan propuesto (porque la IA
falló), **no se abre ningún PR**: nunca se propone borrar el plan por una salida vacía.
