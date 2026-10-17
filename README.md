# whatsthenew

> Pipeline efímero que trae información viva del mercado tech (empleos, sueldos, tendencias,
> empresas y Reddit), la analiza con IA y genera un reporte de propuestas para mantener
> actualizado el plan de carrera (`GOD_PLAN.md`).

`whatsthenew` responde a una pregunta simple: **¿qué está pidiendo el mercado hoy para los roles
que me interesan?** — y lo documenta sin acumular basura en disco ni RAM.

---

## ¿Qué hace?

1. **Trae** datos de fuentes abiertas (APIs, RSS y HTML) para roles de Cloud, DevOps, SRE,
   Platform, Backend, Software, Observabilidad e Infra.
2. **Clasifica** cada aviso por rol, nivel (junior/semi/senior/lead), años y stack.
3. **Analiza** con OpenCode el delta entre lo que pide el mercado y lo que ya dice el plan.
4. **Entrega** `output/PROPOSED_UPDATES.md` con la fuente y la fecha de cada dato.
5. **Purga** los datos crudos temporales al terminar.

Principio heredado: **mide → haz → documenta → apaga/limpia → libera**.

---

## Estructura

```text
whatsthenew/
├── config/            # Catálogos: fuentes, roles y búsquedas de Reddit
├── src/whatsthenew/   # Código del pipeline
│   ├── fetchers/      # Un módulo por familia de fuentes
│   ├── classify.py    # Detección de nivel, años y stack
│   ├── analyze.py     # Puente hacia OpenCode (IA)
│   ├── report.py      # Genera PROPOSED_UPDATES.md
│   ├── cleanup.py     # Purga de temporales
│   └── pipeline.py    # Orquesta todo
├── docs/              # Arquitectura, fuentes, esquema, OpenCode y protección de rama
├── scripts/           # bootstrap, run, cron y protection
├── docker/            # Dockerfile + compose
├── output/            # Entregable (PROPOSED_UPDATES.md)
├── tests/             # Pruebas
└── .opencode/         # Agente y comando de OpenCode
```

---

## Requisitos

- Python 3.11+
- Docker (opcional, para el contenedor efímero)
- OpenCode instalado (`opencode run ...`)
- (Opcional) App OAuth gratuita de Reddit para leer Reddit de forma fiable

---

## Uso rápido

```bash
# 1. Preparar entorno
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Ejecutar el pipeline
python -m whatsthenew run

# 3. Ver el resultado
cat output/PROPOSED_UPDATES.md
```

Con Docker:

```bash
docker compose -f docker/docker-compose.yml run --rm whatsthenew
```

---

## Automatización

El contenedor es **efímero**: se enciende cada 3 días por cron, hace su trabajo y se apaga.
Entre ejecuciones **no consume RAM**. Ver `scripts/cron.example`.

---

## Documentación

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — cómo funciona el pipeline y el uso de recursos
- [`docs/FUENTES.md`](docs/FUENTES.md) — todas las fuentes, endpoints y reglas anti-bloqueo
- [`docs/DATA-SCHEMA.md`](docs/DATA-SCHEMA.md) — el esquema de cada dato (con fuente y fecha)
- [`docs/OPENCODE.md`](docs/OPENCODE.md) — cómo se conecta OpenCode para ordenar los datos
- [`docs/BRANCH-PROTECTION.md`](docs/BRANCH-PROTECTION.md) — protección de la rama `main`
- [`docs/REDDIT-SETUP.md`](docs/REDDIT-SETUP.md) — credenciales de Reddit en `.env`

---

## Licencia

MIT — ver [`LICENSE`](LICENSE).
