#!/usr/bin/env bash
# run.sh — ejecuta el pipeline completo (fetch -> analisis -> purga)
set -euo pipefail

cd "$(dirname "$0")/.."
# shellcheck disable=SC1091
[ -f .venv/bin/activate ] && source .venv/bin/activate

python -m whatsthenew run
echo "Reporte: output/PROPOSED_UPDATES.md"
