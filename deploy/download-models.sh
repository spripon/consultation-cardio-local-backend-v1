#!/usr/bin/env bash
# PHASE INSTALLATION UNIQUEMENT — télécharge les modèles locaux sur l'hôte.
# Jamais exécuté au runtime : le conteneur API tourne hors ligne
# (HF_HUB_OFFLINE=1 / OPENMED_OFFLINE=1) et n'a aucune route de sortie
# (réseau Docker `internal: true`). Aucun poids n'est committé (deploy/models/
# est ignoré par Git).
#
# Usage :
#   bash deploy/download-models.sh                # modèle PII français seul
#   bash deploy/download-models.sh --with-speech  # + faster-whisper small
set -euo pipefail

cd "$(dirname "$0")/.."

WITH_SPEECH=0
for arg in "$@"; do
  case "$arg" in
    --with-speech) WITH_SPEECH=1 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "Option inconnue : $arg" >&2; exit 2 ;;
  esac
done

OUT="deploy/models"
mkdir -p "$OUT"

# Ubuntu récent applique PEP 668 (« externally managed environment ») et refuse
# `pip install --user`. On utilise donc un venv local dédié, idempotent, ignoré
# par Git et par le contexte Docker.
VENV="deploy/.venv-models"
BOOTSTRAP=${PYTHON:-python3}
command -v "$BOOTSTRAP" >/dev/null 2>&1 || { echo "python3 requis (paquets python3 + python3-venv)" >&2; exit 1; }

if [ ! -x "$VENV/bin/python" ]; then
  echo "→ Création du venv d'installation : $VENV"
  "$BOOTSTRAP" -m venv "$VENV"
fi
PY="$VENV/bin/python"
"$PY" -m pip install --quiet --upgrade pip
# Modèles publics : aucun jeton Hugging Face requis.
"$PY" -m pip install --quiet --upgrade huggingface_hub

if [ -n "$(ls -A "$OUT/openmed-pii-fr" 2>/dev/null)" ]; then
  echo "= $OUT/openmed-pii-fr déjà présent : téléchargement PII ignoré."
else
  echo "== Modèle PII français (OpenMed 2.0) =="
  "$PY" scripts/download_openmed_model.py --out "$OUT" --skip-whisper
fi

if [ "$WITH_SPEECH" -eq 1 ]; then
  if [ -n "$(ls -A "$OUT/faster-whisper-small" 2>/dev/null)" ]; then
    echo "= $OUT/faster-whisper-small déjà présent : téléchargement Whisper ignoré."
  else
    echo "== Modèle dictée locale (faster-whisper small, CTranslate2) =="
    # Même script, même mécanisme reproductible (snapshot Hugging Face du dépôt
    # Systran/faster-whisper-small vers deploy/models/faster-whisper-small).
    "$PY" scripts/download_openmed_model.py --out "$OUT" --skip-pii
  fi
else
  echo "= Dictée non demandée : modèle Whisper non téléchargé (ENABLE_SPEECH=false)."
fi

cat <<'INFO'

✓ Phase installation terminée.

Le runtime redevient hors ligne automatiquement : HF_HUB_OFFLINE=1 et
TRANSFORMERS_OFFLINE=1 sont fixés dans deploy/docker-compose.yml, et
backend/.env doit conserver HF_HUB_OFFLINE=true / OPENMED_OFFLINE=true.

Les modèles sont montés en lecture seule dans le conteneur sous /models :
  OPENMED_PII_MODEL=/models/openmed-pii-fr
  WHISPER_MODEL_PATH=/models/faster-whisper-small   (si ENABLE_SPEECH=true)

Vérifier ensuite : bash deploy/preflight-ubuntu.sh
INFO
