#!/usr/bin/env bash
# Vérifie qu'aucun appel réseau sortant vers un service cloud d'IA ne subsiste
# dans le code applicatif (frontend + backend).
set -euo pipefail

cd "$(dirname "$0")/.."

PATTERNS=(
  "api\.openai\.com"
  "openai"
  "anthropic"
  "googleapis\.com"
  "generativelanguage"
  "azure\.com/openai"
  "supabase"
  "ai\.gateway\.lovable\.dev"
  "OPENAI_API_KEY"
)

STATUS=0
for pattern in "${PATTERNS[@]}"; do
  if matches=$(grep -rniE "$pattern" src backend/app 2>/dev/null); then
    echo "✗ Référence cloud interdite trouvée pour /$pattern/ :"
    echo "$matches"
    STATUS=1
  fi
done

if [ "$STATUS" -eq 0 ]; then
  echo "✓ Aucun appel à un service d'IA externe détecté dans src/ et backend/app/."
fi
exit "$STATUS"