#!/usr/bin/env bash
# server-install.sh — prepara el servidor (Debian/Ubuntu + Docker) para la
# ejecución semanal. Idempotente: se puede volver a ejecutar sin miedo.
#
#   git clone https://github.com/bulletformyvalentinefan/whatsthenew.git
#   cd whatsthenew
#   ./scripts/server-install.sh
#
# Deja:
#   - la imagen publicada descargada desde GHCR (el servidor no compila nada),
#   - `~/.config/systemd/user/whatsthenew.{service,timer}` habilitados,
#   - un `.env` de plantilla que TÚ completas (token del repo privado + clave del modelo).
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
IMAGE="ghcr.io/bulletformyvalentinefan/whatsthenew:latest"

say() { printf '\n\033[1;36m%s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

# --- 1. Requisitos ---------------------------------------------------------
say "1/5  Comprobando Docker"
command -v docker >/dev/null 2>&1 || die "Docker no está instalado. https://docs.docker.com/engine/install/debian/"
docker info >/dev/null 2>&1 || die "No puedo hablar con el demonio de Docker (¿permisos? añade tu usuario al grupo 'docker')."
docker compose version >/dev/null 2>&1 || die "Falta el plugin 'docker compose'."

# --- 2. .env ---------------------------------------------------------------
say "2/5  Preparando .env"
if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env
  echo "Creado .env (chmod 600). COMPLÉTALO antes de la primera ejecución:"
  echo "  - PLAN_REPO_TOKEN  (token con acceso al repo privado del plan)"
  echo "  - OPENROUTER_API_KEY (o el proveedor que uses)"
  echo "  - OPENCODE_MODEL"
else
  echo ".env ya existe: no lo toco."
fi

# --- 3. Imagen -------------------------------------------------------------
say "3/5  Descargando la imagen desde GHCR"
if ! docker pull "$IMAGE"; then
  echo "No se pudo descargar. Si el paquete es privado, inicia sesión primero:"
  echo "  echo \$GHCR_TOKEN | docker login ghcr.io -u TU_USUARIO --password-stdin"
  die "docker pull falló para $IMAGE"
fi

# --- 4. Utilidades systemd de usuario ------------------------------------
say "4/5  Instalando el timer semanal (systemd --user)"
UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"
cp systemd/whatsthenew.service systemd/whatsthenew.timer "$UNIT_DIR/"
# El servicio usa %h/whatsthenew; asegúrate de que el repo está ahí.
if [ "$(pwd)" != "$HOME/whatsthenew" ]; then
  echo "AVISO: el repo está en $ROOT, no en $HOME/whatsthenew."
  echo "       Clónalo en $HOME/whatsthenew (el servicio apunta ahí) o edita WorkingDirectory."
fi
systemctl --user daemon-reload
systemctl --user enable --now whatsthenew.timer
# Mantener el timer vivo aunque el usuario no tenga sesión abierta.
loginctl enable-linger "$USER" || echo "AVISO: no pude habilitar linger (ejecuta: sudo loginctl enable-linger $USER)"

# --- 5. Prueba manual opcional -------------------------------------------
say "5/5  Listo"
echo "Estado del timer:"
systemctl --user list-timers whatsthenew.timer --no-pager || true
echo
echo "Ejecución manual de prueba:"
echo "  docker compose -f docker/docker-compose.server.yml run --rm whatsthenew"
echo
echo "Logs:"
echo "  journalctl --user -u whatsthenew.service -n 100 --no-pager"
