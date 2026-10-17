# Reddit — sin credenciales (y credenciales opcionales)

Reddit es la fuente más fuerte del proyecto. **No hace falta cuenta, app ni aprobación**:
el pipeline obtiene lo que necesitamos (tema, fecha y **nº de respuestas** de cada hilo) sin login.

## Cómo funciona (en orden)

1. **PullPush** (espejo público de Reddit) — camino principal.
   En **una sola petición** por `(subreddit, consulta)` devuelve `title`, `created_utc` y
   `num_comments`. Endpoint configurable con `PULLPUSH_URL`.
2. **RSS de Reddit** — respaldo si PullPush no responde.
   Baja la búsqueda (`.rss`) y, para los **top N** hilos por búsqueda (`REDDIT_REPLIES_TOP_N`),
   lee el feed de comentarios del hilo (`/comments/<id>/.rss`) para contar respuestas.
3. **OAuth** — opcional, solo si algún día hay credenciales.

Si una fuente devuelve `429`, el cliente reintenta con espera creciente (`REDDIT_RETRIES`).

## ¿Por qué no uso la API oficial por defecto?

La **Responsible Builder Policy** de Reddit (oct-2026) exige **aprobación previa** para usar su
API. Además, sin token, Reddit bloquea con `403`/`429` los feeds desde muchas IPs. Por eso el
camino por defecto es **PullPush**, que no requiere login.

## Credenciales (opcionales)

> Solo si algún día consigues acceso aprobado a la API. Viven **solo** en `.env`, protegido por
> `.gitignore`. Nunca se versionan.

1. Crea una app en <https://www.reddit.com/prefs/apps> (tipo **script**,
   redirect uri `http://localhost:8080`).
2. Copia `client_id` (bajo el nombre) y `secret`.
3. Rellena en `.env`:

```text
REDDIT_CLIENT_ID=tu_client_id
REDDIT_CLIENT_SECRET=tu_secret
USER_AGENT=whatsthenew/0.1 (market watcher by tu_usuario_reddit)
```

Con credenciales, el cliente hace **login primero** (`client_credentials`) y luego las búsquedas,
una cada `REDDIT_DELAY_SECONDS` (10 s por defecto).

## Seguridad

| Archivo | ¿Se versiona? | Contenido |
|---|---|---|
| `.env` | ❌ No (ignorado) | Credenciales reales (si las hay) |
| `.env.example` | ✅ Sí | Plantilla vacía, sin secretos |

`./scripts/check-secrets.sh` (y el paso de CI) falla si un secreto llega al repositorio.

Verifica que `.env` no se sube:

```bash
git check-ignore -v .env   # debe responder .gitignore:...:.env
git status --short         # .env NO debe aparecer
```
