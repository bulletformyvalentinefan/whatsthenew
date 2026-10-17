#!/usr/bin/env bash
# bootstrap.sh — prepara el entorno local de whatsthenew
set -euo pipefail

cd "$(dirname "$0")/.."
echo "== whatsthenew bootstrap =="

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Creado .env desde .env.example"
fi

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

echo "Listo. Activa el entorno con: source .venv/bin/activate"
echo "Ejecuta el pipeline con:      python -m whatsthenew run"
