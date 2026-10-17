# Despliegue en el servidor — whatsthenew

Cómo dejar corriendo el pipeline **una vez por semana** en un servidor con Docker,
sin que consuma recursos entre ejecuciones.

Arquitectura completa:

```text
   GitHub (público)                      GitHub (privado)          Tu servidor (Debian + Docker)
 ┌────────────────────┐                ┌──────────────────┐       ┌───────────────────────────┐
 │ whatsthenew        │  Actions       │ god-plan         │       │ systemd timer (semanal)   │
 │  · código          │ ──build──▶ GHCR │  · GOD_PLAN.md   │◀─PR── │  docker compose run --rm  │
 │  · imagen Docker   │                │  · proposals/    │       │  └─ contenedor efímero    │
 └────────────────────┘                └──────────────────┘       └───────────────────────────┘
            │                                    ▲                             │
            └──────── docker pull ───────────────┘        fetch + OpenCode + PR ┘
```

- El **repositorio público** solo tiene código. La imagen la construye GitHub y la
  publica en GHCR (`ghcr.io/bulletformyvalentinefan/whatsthenew:latest`).
- El **repositorio privado** (`god-plan`) guarda `GOD_PLAN.md`. Nadie más lo ve.
- El **servidor** solo descarga la imagen y la ejecuta con un timer semanal.

---

## 0. Requisitos en el servidor

- Docker Engine + plugin `docker compose`.
- Tu usuario en el grupo `docker` (`sudo usermod -aG docker $USER` y reconectar).
- Salida a internet (fuentes + proveedor del modelo + GitHub).

> El contenedor usa **~200–500 MB de RAM** y muere al terminar. La inferencia del
> modelo corre **fuera** (en el proveedor), así que el servidor no hace trabajo pesado.

---

## 1. La imagen (se construye sola en GitHub)

No haces nada: al hacer push a `main`, el workflow
[`.github/workflows/docker.yml`](../.github/workflows/docker.yml) construye y publica
la imagen en GHCR.

**Haz el paquete público** una sola vez (contiene solo código, ningún secreto):
`GitHub → tu perfil → Packages → whatsthenew → Package settings → Change visibility → Public`.

Si prefieres dejarlo privado, en el servidor haz `docker login ghcr.io` con un token
**clásico** que tenga `read:packages` (los tokens fine-grained no cubren GHCR):

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u bulletformyvalentinefan --password-stdin
```

---

## 2. El plan, en su repositorio privado

Sigue [`docs/PLAN-REPO.md`](PLAN-REPO.md) para crear el repo privado `god-plan` y el
token. Resumen: crea el repo privado con `GOD_PLAN.md`, y genera un **token fine-grained**
con permiso solo sobre él (`contents:write`, `pull_requests:write`).

---

## 3. Instalar en el servidor

```bash
# en el servidor (usuario normal, con docker)
cd "$HOME"
git clone https://github.com/bulletformyvalentinefan/whatsthenew.git
cd whatsthenew
./scripts/server-install.sh
```

El script:

1. comprueba Docker,
2. crea `.env` (chmod 600) a partir de `.env.example`,
3. descarga la imagen de GHCR,
4. instala y activa el **timer semanal** de systemd (`systemd/whatsthenew.{service,timer}`).

Luego edita el `.env` y completa **solo esto**:

```bash
PLAN_REPO=bulletformyvalentinefan/god-plan
PLAN_REPO_TOKEN=<token fine-grained>
OPENCODE_MODEL=openrouter/deepseek/deepseek-v4.1-flash:decart
OPENROUTER_API_KEY=<tu clave>
PUBLISH_PROPOSAL=1
```

---

## 4. Probar una vez a mano

```bash
cd "$HOME/whatsthenew"
docker compose -f docker/docker-compose.server.yml run --rm whatsthenew
```

Si todo va bien: se genera `output/PROPOSED_UPDATES.md`, y aparece un **PR** en el
repositorio privado `god-plan`. Revísalo, mira el diff y fusiónalo si estás de acuerdo.

---

## 5. Activarlo

```bash
systemctl --user list-timers whatsthenew.timer   # ver próxima ejecución
systemctl --user start whatsthenew.service       # forzar ahora
journalctl --user -u whatsthenew.service -n 100  # ver logs

# para que corra aunque no tengas sesión abierta:
sudo loginctl enable-linger "$USER"
```

El timer dispara **cada lunes a las 04:00** y, si el servidor estaba apagado, se
recupera al arrancar (`Persistent=true`).

---

## Alternativa: cron

Si prefieres cron a systemd, copia la línea de
[`scripts/cron.example`](../scripts/cron.example) en `crontab -e`.

---

## Coste y recursos

| Concepto | Dónde | Nota |
|---|---|---|
| CPU / RAM del servidor | Servidor | ~200–500 MB, solo durante la corrida |
| RAM en espera | — | **0 MB** (no hay contenedor encendido) |
| Inferencia del modelo | Proveedor (OpenRouter…) | Es el coste real: **tokens** |
| Disco | Servidor | Imagen (~400 MB) + JSON temporal (se borra) |

Para abaratar: un modelo más pequeño, o recortar el volumen de datos que se le pasan.

---

## Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `docker pull` 403/404 | Paquete GHCR privado | Hazlo público o `docker login ghcr.io` |
| No aparece el PR | Falta `PLAN_REPO_TOKEN` o `PUBLISH_PROPOSAL=1` | Revisa el `.env` y los logs |
| El análisis se queda en el respaldo | OpenCode o el modelo fallan | Mira `journalctl`; el reporte determinista ya está escrito |
| Reddit 403/429 | Bloqueo por IP/ritmo | Sube `REDDIT_DELAY_SECONDS` y `HTTP_DELAY_SECONDS` |
