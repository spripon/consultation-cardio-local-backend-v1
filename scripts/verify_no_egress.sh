#!/usr/bin/env bash
# Vérifie qu'aucun appel réseau sortant vers un service cloud ne subsiste dans
# le code exécutable au runtime (frontend + backend + scripts runtime).
#
# La documentation (docs/, README) et le script de téléchargement initial des
# modèles (scripts/download_openmed_model.py, exécuté hors production sur
# l'hôte) sont volontairement exclus : ils contiennent des URL d'installation
# nécessaires mais ne sont jamais appelés pendant le traitement d'un document.
set -euo pipefail

cd "$(dirname "$0")/.."

# Cibles cloud strictement interdites dans le code exécutable.
FORBIDDEN=(
  "api\.openai\.com"
  "openai"
  "openai\.azure"
  "anthropic"
  "deepseek"
  "googleapis\.com"
  "generativelanguage"
  "azure\.com/openai"
  "azure\.com"
  "supabase"
  "ai\.gateway\.lovable\.dev"
  "lovable\.dev"
  "OPENAI_API_KEY"
  "ocr_engine=mock"
)

# Portée : le code réellement exécuté au runtime (frontend, backend et scripts
# runtime). Seul scripts/download_openmed_model.py est exclu : étape
# d'installation hors runtime, exécutée manuellement sur l'hôte.
SCOPE=(src backend/app scripts)
EXCLUDE_RE='^(scripts/download_openmed_model\.py|scripts/verify_no_egress\.sh|src/lib/legacyCleanup\.ts):'


STATUS=0
for pattern in "${FORBIDDEN[@]}"; do
  # src/lib/legacyCleanup.ts est exclu : il ne contient qu'une liste de clés
  # d'API héritées à SUPPRIMER du navigateur, aucun appel réseau.
  if matches=$(grep -rniE "$pattern" "${SCOPE[@]}" 2>/dev/null \
      | grep -vE "$EXCLUDE_RE"); then
    echo "✗ Référence cloud interdite trouvée pour /$pattern/ :"
    echo "$matches"
    STATUS=1
  fi
done

# Aucune URL absolue http(s) ne doit apparaître dans le code exécutable :
# tous les appels doivent être relatifs à la même origine.
if urls=$(grep -rnoE "https?://[A-Za-z0-9.-]+" "${SCOPE[@]}" 2>/dev/null \
    | grep -vE "$EXCLUDE_RE" \
    | grep -viE "127\.0\.0\.1|localhost|www\.w3\.org|schema\.org|example\.invalid"); then
  echo "✗ URL absolue interdite dans le code exécutable :"
  echo "$urls"
  STATUS=1
fi

# Aucun moteur factice ne doit rester dans le pipeline.
if mocks=$(grep -rniE "mock|fake" backend/app 2>/dev/null); then
  echo "✗ Moteur factice (mock/fake) détecté dans le backend :"
  echo "$mocks"
  STATUS=1
fi

if [ "$STATUS" -eq 0 ]; then
  echo "✓ Aucun appel réseau externe ni moteur factice détecté dans src/ et backend/app/."
fi
exit "$STATUS"