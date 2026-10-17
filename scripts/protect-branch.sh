#!/usr/bin/env bash
# protect-branch.sh — protege la rama principal con un ruleset de GitHub.
#
# Usa la API de rulesets: no requiere que la rama exista todavia en el remoto.
# Requiere `gh` autenticado con permisos de admin sobre el repositorio.
#
# Uso:
#   ./scripts/protect-branch.sh [owner/repo]
set -euo pipefail

cd "$(dirname "$0")/.."

REPO="${1:-}"
if [ -z "$REPO" ]; then
  if git remote get-url origin >/dev/null 2>&1; then
    REPO="$(git remote get-url origin | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')"
  else
    REPO="bulletformyvalentinefan/whatsthenew"
  fi
fi

BRANCH="${BRANCH:-main}"
RULESET_NAME="protect-${BRANCH}"

echo "== Protegiendo $REPO -> refs/heads/$BRANCH =="

# ¿Ya existe el ruleset?
EXISTING_ID="$(gh api "repos/$REPO/rulesets" --jq ".[] | select(.name==\"$RULESET_NAME\") | .id" 2>/dev/null || true)"

BODY=$(cat <<JSON
{
  "name": "$RULESET_NAME",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/$BRANCH"],
      "exclude": []
    }
  },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "required_linear_history" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
      }
    }
  ]
}
JSON
)

if [ -n "$EXISTING_ID" ]; then
  echo "Actualizando ruleset existente (id=$EXISTING_ID)..."
  printf '%s' "$BODY" | gh api --method PUT "repos/$REPO/rulesets/$EXISTING_ID" --input - >/dev/null
else
  echo "Creando ruleset nuevo..."
  printf '%s' "$BODY" | gh api --method POST "repos/$REPO/rulesets" --input - >/dev/null
fi

echo "OK. Reglas activas:"
gh api "repos/$REPO/rulesets" --jq '.[] | "  - \(.name) [\(.enforcement)] -> \(.conditions.ref_name.include // ["(ver detalle)"] | join(", "))"' || true
