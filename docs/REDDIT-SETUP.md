# Configurar las credenciales de Reddit

Reddit es la fuente más fuerte del proyecto, así que conviene usar su **API oficial** (no scraping).
Con una app OAuth gratuita se obtienen **100 peticiones/minuto** y se evita el `429` que aparece en
las consultas sin token.

> Las credenciales viven **solo** en `.env`, que está protegido por `.gitignore`. Nunca se versionan.

## 1. Crear la app

1. Inicia sesión en Reddit y entra a <https://www.reddit.com/prefs/apps>.
2. Pulsa **"create another app..."**.
3. Completa:
   - **name**: `whatsthenew` (o el que prefieras)
   - **type**: **script**
   - **redirect uri**: `http://localhost:8080` (no se usa con `client_credentials`, pero es obligatorio)
4. Guarda con **"create app"**.

## 2. Copiar las credenciales

En la tarjeta de tu app verás:

- **client_id**: la cadena corta **justo debajo** del nombre de la app.
- **secret**: el campo marcado como *secret*.

```text
REDDIT_CLIENT_ID=tu_client_id
REDDIT_CLIENT_SECRET=tu_secret
REDDIT_USER_AGENT=whatsthenew/0.1 by tu_usuario_reddit
```

## 3. Escribirlas en `.env`

```bash
cp .env.example .env   # si aún no existe
chmod 600 .env         # solo tu usuario puede leerlo
# edita .env y rellena las 3 variables
```

Verifica que `.env` **no** se sube a git:

```bash
git check-ignore -v .env   # debe responder .gitignore:...:.env
git status --short         # .env NO debe aparecer
```

## 4. Probar que funciona

```bash
python -m whatsthenew run
```

Si el token es válido, en los logs no verás `429` en las consultas de Reddit. Sin token, el cliente
cae automáticamente al modo RSS con pausas de 10 s.

## Seguridad

| Archivo | ¿Se versiona? | Contenido |
|---|---|---|
| `.env` | ❌ No (ignorado) | Credenciales reales |
| `.env.example` | ✅ Sí | Plantilla vacía, sin secretos |

Si alguna vez una credencial se filtra, revócala en <https://www.reddit.com/prefs/apps> y genera una
nueva. Rotar es más barato que limpiar un secreto del historial de git.
