#!/usr/bin/env bash
# check-secrets.sh — evita que un secreto llegue al repositorio público.
#
# Falla si:
#   1. `.env` quedó rastreado por git.
#   2. Hay valores no vacíos de variables sensibles en archivos versionados.
#   3. Hay claves privadas versionadas.
set -euo pipefail

cd "$(dirname "$0")/.."
fail=0

# 1) .env no debe estar rastreado
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  echo "ERROR: .env está rastreado por git."
  fail=1
fi

# 2) variables sensibles con valor no vacío en archivos versionados
if git grep -nE '(REDDIT_CLIENT_SECRET|REDDIT_CLIENT_ID|DISCORD_WEBHOOK|GITHUB_TOKEN|AWS_SECRET_ACCESS_KEY)=[^[:space:]]+' -- \
    ':!.env.example' ':!docs/*' ':!*.md' >/dev/null 2>&1; then
  echo "ERROR: posible secreto versionado (revisa la salida de git grep)."
  git grep -nE '(REDDIT_CLIENT_SECRET|REDDIT_CLIENT_ID|DISCORD_WEBHOOK|GITHUB_TOKEN|AWS_SECRET_ACCESS_KEY)=[^[:space:]]+' -- \
    ':!.env.example' ':!docs/*' ':!*.md' || true
  fail=1
fi

# 3) claves privadas versionadas
if git grep -nIE 'BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY' >/dev/null 2>&1; then
  echo "ERROR: clave privada versionada."
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "OK: no se detectaron secretos en archivos versionados."
fi
exit "$fail"
