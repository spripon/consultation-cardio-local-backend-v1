#!/usr/bin/env bash
# Preflight lecture seule pour le mode Cloudflare Tunnel.
# Cible locale : http://127.0.0.1:8091 -> cardio-web:80.
set -euo pipefail

cd "$(dirname "$0")/.."
STATUS=0
ok()   { echo "OK  $*"; }
fail() { echo "ERR $*"; STATUS=1; }
warn() { echo "WARN $*"; }

echo "== Preflight Ubuntu - mode Cloudflare Tunnel =="

echo "Cible publique : https://consultation.cardiologie-tarbes.org"
echo "Origine tunnel : http://127.0.0.1:8091"
echo

# Systeme
if [ "$(uname -s)" != "Linux" ]; then
  fail "Systeme non Linux : cette pile cible Ubuntu."
elif [ -r /etc/os-release ]; then
  . /etc/os-release
  case "${ID:-}${ID_LIKE:-}" in
    *ubuntu*|*debian*) ok "Distribution : ${PRETTY_NAME:-inconnue}" ;;
    *) warn "Distribution non Ubuntu/Debian : ${PRETTY_NAME:-inconnue}" ;;
  esac
fi

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|aarch64) ok "Architecture : $ARCH" ;;
  *) fail "Architecture non supportee : $ARCH" ;;
esac

MEM_MB=$(awk '/MemTotal/ {printf "%d", $2/1024}' /proc/meminfo 2>/dev/null || echo 0)
if [ "$MEM_MB" -ge 7500 ]; then ok "RAM : ${MEM_MB} Mo"
elif [ "$MEM_MB" -ge 3500 ]; then warn "RAM : ${MEM_MB} Mo (8 Go recommandes)"
else fail "RAM insuffisante : ${MEM_MB} Mo"; fi

DISK_MB=$(df -Pm . | awk 'NR==2 {print $4}')
if [ "$DISK_MB" -ge 15000 ]; then ok "Disque libre : ${DISK_MB} Mo"
elif [ "$DISK_MB" -ge 8000 ]; then warn "Disque libre : ${DISK_MB} Mo (15 Go recommandes)"
else fail "Espace disque insuffisant : ${DISK_MB} Mo"; fi

need() {
  if command -v "$1" >/dev/null 2>&1; then ok "$1 present"
  else fail "$1 absent"; fi
}
need docker
need git
need python3
if command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1; then
  ok "curl ou wget present"
else
  fail "ni curl ni wget"
fi

if command -v docker >/dev/null 2>&1; then
  docker compose version >/dev/null 2>&1 && ok "Docker Compose v2 present" || fail "Docker Compose v2 absent"
  docker info >/dev/null 2>&1 && ok "Daemon Docker joignable" || fail "Daemon Docker injoignable"
fi

# Cloudflared existe deja normalement pour planning.cardiologie-tarbes.org.
if command -v cloudflared >/dev/null 2>&1; then
  ok "cloudflared present : $(cloudflared --version 2>/dev/null | head -1)"
else
  warn "cloudflared absent du PATH. Les tests locaux peuvent continuer, mais la publication Internet sera impossible."
fi
if command -v systemctl >/dev/null 2>&1; then
  if systemctl is-active --quiet cloudflared 2>/dev/null; then
    ok "service cloudflared actif"
  else
    warn "service cloudflared non actif ou gere autrement"
  fi
fi

# Port local dedie. 80/443 de l'hote ne sont PAS requis par cette application.
web_container_running() {
  command -v docker >/dev/null 2>&1 || return 1
  [ "$(docker ps --filter 'name=^/cardio-web$' --filter 'status=running' --format '{{.Names}}' 2>/dev/null)" = "cardio-web" ]
}
port_8091_busy() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltnH 2>/dev/null | awk '{print $4}' | grep -qE '(^|:)8091$'
  elif command -v netstat >/dev/null 2>&1; then
    netstat -ltn 2>/dev/null | awk '{print $4}' | grep -qE '(^|:)8091$'
  else
    return 2
  fi
}
set +e
port_8091_busy; PORT_RC=$?
set -e
case "$PORT_RC" in
  0)
    if web_container_running; then
      ok "127.0.0.1:8091 deja utilise par cardio-web attendu"
    else
      fail "port 8091 deja occupe par un autre service. Ne rien arreter automatiquement."
    fi
    ;;
  1) ok "port 8091 libre" ;;
  *) warn "port 8091 non verifiable (ni ss ni netstat)" ;;
esac
ok "ports hote 80/443 non requis en mode Cloudflare Tunnel"

# Configuration locale obligatoire
for f in backend/.env deploy/caddy.env; do
  if [ -f "$f" ]; then ok "$f present"
  else fail "$f manquant - executer deploy/prepare-config.sh"; fi
done

if [ -f deploy/caddy.env ]; then
  HASH_LINE=$(grep -E '^BASIC_AUTH_HASH=' deploy/caddy.env | tail -1 | cut -d= -f2-)
  HASH_VALUE=${HASH_LINE%$'\r'}
  case "$HASH_VALUE" in
    \'*\') HASH_VALUE=${HASH_VALUE#\'}; HASH_VALUE=${HASH_VALUE%\'}; QUOTED=1 ;;
    *) QUOTED=0 ;;
  esac
  if [ -z "$HASH_VALUE" ]; then
    fail "BASIC_AUTH_HASH absent"
  elif ! printf '%s' "$HASH_VALUE" | grep -qE '^\$2[aby]\$[0-9]{2}\$.{20,}$'; then
    fail "BASIC_AUTH_HASH non valide (valeur non affichee)"
  elif printf '%s' "$HASH_VALUE" | grep -qi 'REMPLACER_PAR_LE_HASH'; then
    fail "BASIC_AUTH_HASH encore au placeholder"
  elif [ "$QUOTED" -ne 1 ]; then
    fail "BASIC_AUTH_HASH doit etre entre apostrophes simples"
  else
    ok "BASIC_AUTH_HASH bcrypt single-quoted"
  fi
  perm=$(stat -c '%a' deploy/caddy.env)
  case "$perm" in 600|640|400|440) ok "permissions deploy/caddy.env : $perm" ;; *) warn "chmod 600 deploy/caddy.env recommande" ;; esac
fi

if [ -f backend/.env ]; then
  perm=$(stat -c '%a' backend/.env)
  case "$perm" in 600|640|400|440) ok "permissions backend/.env : $perm" ;; *) warn "chmod 600 backend/.env recommande" ;; esac
fi

# Modeles
if [ -d deploy/models/openmed-pii-fr ] && [ -n "$(ls -A deploy/models/openmed-pii-fr 2>/dev/null)" ]; then
  ok "modele OpenMed PII local present"
else
  fail "deploy/models/openmed-pii-fr absent ou vide"
fi

ENABLE_SPEECH_VALUE=$(grep -E '^ENABLE_SPEECH=' backend/.env 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"'"'"' \r' | tr 'A-Z' 'a-z')
if [ "${ENABLE_SPEECH_VALUE:-false}" = "true" ]; then
  [ -d deploy/models/faster-whisper-small ] && [ -n "$(ls -A deploy/models/faster-whisper-small 2>/dev/null)" ] \
    && ok "modele Whisper local present" \
    || fail "ENABLE_SPEECH=true mais modele Whisper absent"
else
  ok "ENABLE_SPEECH=false : Whisper non requis"
fi

# Verifie que Compose contient bien le binding localhost attendu sans afficher de secrets.
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && [ -f backend/.env ] && [ -f deploy/caddy.env ]; then
  if docker compose -f deploy/docker-compose.yml config 2>/dev/null | grep -q 'host_ip: 127.0.0.1'; then
    ok "Compose publie le web sur loopback"
  else
    warn "impossible de confirmer host_ip 127.0.0.1 via docker compose config"
  fi
fi

echo
if [ "$STATUS" -eq 0 ]; then
  echo "OK - Preflight local reussi. Etape suivante : build/validate puis route Cloudflare."
else
  echo "ERR - Preflight en echec. Corriger les erreurs avant publication."
fi
exit "$STATUS"
