#!/usr/bin/env bash
# Vérifications AVANT déploiement. Lecture seule : ne télécharge rien,
# ne modifie rien, ne tue aucun processus.
set -euo pipefail

cd "$(dirname "$0")/.."
STATUS=0
ok()   { echo "✓ $*"; }
fail() { echo "✗ $*"; STATUS=1; }
warn() { echo "! $*"; }

echo "== Préflight Ubuntu (lecture seule) =="

# --- Système ---
if [ "$(uname -s)" != "Linux" ]; then
  fail "Système non Linux ($(uname -s)) : cette pile cible Ubuntu."
else
  if [ -r /etc/os-release ]; then
    . /etc/os-release
    case "${ID:-}${ID_LIKE:-}" in
      *ubuntu*|*debian*) ok "Distribution : ${PRETTY_NAME:-inconnue}" ;;
      *) warn "Distribution non Ubuntu/Debian (${PRETTY_NAME:-inconnue}) : non testée." ;;
    esac
  else
    warn "/etc/os-release illisible : distribution inconnue."
  fi
fi

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|aarch64) ok "Architecture : $ARCH (CPU-only supporté)" ;;
  *) fail "Architecture non supportée : $ARCH" ;;
esac

# --- Ressources ---
MEM_MB=$(awk '/MemTotal/ {printf "%d", $2/1024}' /proc/meminfo 2>/dev/null || echo 0)
if [ "$MEM_MB" -ge 7500 ]; then ok "RAM totale : ${MEM_MB} Mo"
elif [ "$MEM_MB" -ge 3500 ]; then warn "RAM totale : ${MEM_MB} Mo (8 Go recommandés pour OpenMed + OCR)"
else fail "RAM insuffisante : ${MEM_MB} Mo (minimum pratique 4 Go)"; fi

DISK_MB=$(df -Pm . | awk 'NR==2 {print $4}')
if [ "$DISK_MB" -ge 15000 ]; then ok "Espace disque libre : ${DISK_MB} Mo"
elif [ "$DISK_MB" -ge 8000 ]; then warn "Espace disque libre : ${DISK_MB} Mo (15 Go recommandés : images + modèles)"
else fail "Espace disque insuffisant : ${DISK_MB} Mo"; fi

# --- Outils ---
need() {
  if command -v "$1" >/dev/null 2>&1; then ok "$1 présent ($(command -v "$1"))"
  else fail "$1 absent — voir deploy/install-host-deps.sh"; fi
}
need docker
need git
need python3
if command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1; then
  ok "curl ou wget présent"
else
  fail "ni curl ni wget — voir deploy/install-host-deps.sh"
fi

if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    ok "Docker Compose v2 : $(docker compose version | head -1)"
  else
    fail "Docker Compose v2 absent (plugin docker-compose-plugin requis)"
  fi
  if docker info >/dev/null 2>&1; then
    ok "Daemon Docker joignable par l'utilisateur courant"
  else
    fail "Daemon Docker injoignable (démarrer docker, ou ajouter l'utilisateur au groupe docker puis rouvrir la session)"
  fi
fi

# --- Ports 80/443 (aucun processus n'est arrêté) ---
# Un port occupé par le conteneur attendu `cardio-web` déjà démarré n'est PAS
# une erreur : `make up` reste idempotent sur une pile en cours d'exécution.
web_container_running() {
  command -v docker >/dev/null 2>&1 || return 1
  [ "$(docker ps --filter 'name=^/cardio-web$' --filter 'status=running' --format '{{.Names}}' 2>/dev/null)" = "cardio-web" ]
}
port_busy() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltnH 2>/dev/null | awk '{print $4}' | grep -qE "[:.]$1\$"
  elif command -v netstat >/dev/null 2>&1; then
    netstat -ltn 2>/dev/null | awk '{print $4}' | grep -qE "[:.]$1\$"
  else
    return 2
  fi
}
WEB_RUNNING=0
web_container_running && WEB_RUNNING=1
for p in 80 443; do
  set +e; port_busy "$p"; rc=$?; set -e
  case "$rc" in
    0)
      if [ "$WEB_RUNNING" -eq 1 ]; then
        echo "i Port $p occupé par le conteneur attendu cardio-web (déjà démarré) : OK"
      else
        fail "Port $p occupé par un autre service : libérer manuellement (aucun processus n'est arrêté par ce script)"
      fi
      ;;
    1) ok "Port $p libre" ;;
    *) warn "Port $p non vérifiable (ni ss ni netstat)" ;;
  esac
done

# --- Configuration obligatoire ---
for f in backend/.env deploy/caddy.env; do
  if [ -f "$f" ]; then ok "$f présent"
  else fail "$f MANQUANT — exécuter deploy/prepare-config.sh puis compléter le fichier"; fi
done

if [ -f deploy/caddy.env ]; then
  if grep -qE '^BASIC_AUTH_HASH=\$2[aby]\$' deploy/caddy.env; then
    ok "BASIC_AUTH_HASH renseigné (valeur non affichée)"
  else
    fail "BASIC_AUTH_HASH absent ou non hashé dans deploy/caddy.env"
  fi
  perm=$(stat -c '%a' deploy/caddy.env)
  case "$perm" in
    600|640|400|440) ok "Permissions deploy/caddy.env : $perm" ;;
    *) warn "Permissions deploy/caddy.env : $perm (recommandé : chmod 600)" ;;
  esac
fi
if [ -f backend/.env ]; then
  perm=$(stat -c '%a' backend/.env)
  case "$perm" in
    600|640|400|440) ok "Permissions backend/.env : $perm" ;;
    *) warn "Permissions backend/.env : $perm (recommandé : chmod 600)" ;;
  esac
fi

# --- Modèles locaux (montés en /models dans le conteneur) ---
if [ -d deploy/models/openmed-pii-fr ] && [ -n "$(ls -A deploy/models/openmed-pii-fr 2>/dev/null)" ]; then
  ok "Modèle PII local : deploy/models/openmed-pii-fr"
else
  fail "deploy/models/openmed-pii-fr absent ou vide — exécuter deploy/download-models.sh (phase installation)"
fi

ENABLE_SPEECH_VALUE=$(grep -E '^ENABLE_SPEECH=' backend/.env 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"'"'"' \r' | tr 'A-Z' 'a-z')
if [ "${ENABLE_SPEECH_VALUE:-false}" = "true" ]; then
  if [ -d deploy/models/faster-whisper-small ] && [ -n "$(ls -A deploy/models/faster-whisper-small 2>/dev/null)" ]; then
    ok "Modèle dictée local : deploy/models/faster-whisper-small"
  else
    fail "ENABLE_SPEECH=true mais deploy/models/faster-whisper-small absent — exécuter deploy/download-models.sh --with-speech"
  fi
else
  ok "ENABLE_SPEECH=false : modèle Whisper non requis"
fi

# --- Frontend statique ---
# Le frontend est compilé DANS l'image web (deploy/Dockerfile.web) : aucun
# Node/npm ni dist/ n'est requis sur l'hôte.
ok "Frontend construit dans l'image Docker web (aucun dist/ hôte requis)"

echo
if [ "$STATUS" -eq 0 ]; then
  echo "✓ Préflight OK : la pile peut être démarrée (make up)."
else
  echo "✗ Préflight en échec : corriger les points ✗ ci-dessus avant tout démarrage."
fi
exit "$STATUS"
