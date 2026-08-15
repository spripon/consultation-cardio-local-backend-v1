#!/usr/bin/env bash
# Validation locale du mode Cloudflare Tunnel.
# Par defaut : audit + compose + build, sans demarrage.
# --start : demarre la pile et exige local Caddy 401 + health 200 + readyz 200.
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE_FILE=deploy/docker-compose.yml
COMPOSE=(docker compose -f "$COMPOSE_FILE")
START=0
LOCAL_ORIGIN="http://127.0.0.1:8091"

for arg in "$@"; do
  case "$arg" in
    --start) START=1 ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) echo "Option inconnue : $arg" >&2; exit 2 ;;
  esac
done

echo "== 1/4 Audit no-egress statique =="
bash scripts/verify_no_egress.sh

echo
echo "== 2/4 Validation Docker Compose =="
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  echo "ERR docker / docker compose v2 absent" >&2
  exit 1
fi
"${COMPOSE[@]}" config >/dev/null
echo "OK docker compose config"

echo
echo "== 3/4 Construction images api + web =="
"${COMPOSE[@]}" build

echo
echo "== 4/4 Demarrage et sondes locales =="
if [ "$START" -eq 0 ]; then
  echo "Validation build terminee sans demarrage."
  echo "Utiliser : bash deploy/validate-install.sh --start"
  exit 0
fi

bash deploy/preflight-ubuntu.sh
"${COMPOSE[@]}" up -d

STATUS=0

# A. Caddy local : HTTP attendu car TLS est termine par Cloudflare.
echo "-> Origine locale : $LOCAL_ORIGIN sans identifiants"
CODE=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 "$LOCAL_ORIGIN/" || echo "000")
if [ "$CODE" = "401" ]; then
  echo "OK Basic Auth local actif : HTTP 401"
else
  echo "ERR attendu HTTP 401 sur $LOCAL_ORIGIN, obtenu $CODE"
  STATUS=1
fi

# B. Verifie que le port n'ecoute que sur loopback si ss est disponible.
if command -v ss >/dev/null 2>&1; then
  LISTEN_LINE=$(ss -ltnH 2>/dev/null | awk '$4 ~ /:8091$/ {print $4}' | head -1 || true)
  case "$LISTEN_LINE" in
    127.0.0.1:8091) echo "OK port 8091 lie uniquement a 127.0.0.1" ;;
    "") echo "ERR aucun listener 8091 detecte"; STATUS=1 ;;
    *) echo "ERR port 8091 ecoute sur une adresse inattendue : $LISTEN_LINE"; STATUS=1 ;;
  esac
fi

# C. API directement dans le conteneur interne.
probe_api() {
  local path="$1"
  "${COMPOSE[@]}" exec -T api python -c "
import sys, urllib.request
try:
    with urllib.request.urlopen('http://127.0.0.1:8000$path', timeout=10) as r:
        print(r.status); print(r.read().decode()[:600])
except urllib.error.HTTPError as e:
    print(e.code); print(e.read().decode()[:600])
except Exception as e:
    print(0); print(type(e).__name__)
" 2>/dev/null
}

echo "-> Attente API (30 s max)"
for _ in $(seq 1 30); do
  [ "$(probe_api /api/v1/health | head -1)" = "200" ] && break
  sleep 1
done

HEALTH=$(probe_api /api/v1/health)
HEALTH_CODE=$(echo "$HEALTH" | head -1)
echo "health -> HTTP $HEALTH_CODE"
[ "$HEALTH_CODE" = "200" ] || STATUS=1

READY=$(probe_api /api/v1/readyz)
READY_CODE=$(echo "$READY" | head -1)
echo "readyz -> HTTP $READY_CODE"
if [ "$READY_CODE" != "200" ]; then
  STATUS=1
  MISSING=$(echo "$READY" | tail -n +2 | python3 -c "
import json, sys
try:
    print(', '.join(json.load(sys.stdin).get('missing') or []) or 'inconnu')
except Exception:
    print('reponse non exploitable')
" 2>/dev/null || echo "inconnu")
  echo "ERR API non prete. Composants manquants : $MISSING"
fi

# D. Test dynamique no-egress API.
echo "-> Test no-egress dynamique du conteneur API"
set +e
"${COMPOSE[@]}" exec -T api python -c "
import socket,sys
try:
    socket.create_connection(('1.1.1.1',443),timeout=4)
except Exception as e:
    print('NO-EGRESS OK:', type(e).__name__); sys.exit(0)
print('EGRESS DETECTE'); sys.exit(1)
"
EGRESS_RC=$?
set -e
if [ "$EGRESS_RC" -eq 0 ]; then
  echo "OK API sans connexion TCP sortante"
else
  echo "ERR API peut etablir une connexion TCP sortante"
  STATUS=1
fi

echo
if [ "$STATUS" -eq 0 ]; then
  echo "OK Validation locale complete : localhost:8091=401, health=200, readyz=200, no-egress OK."
  echo "Etape suivante : configurer/valider le Published application Cloudflare Tunnel."
else
  echo "ERR Validation locale en echec. Ne pas publier de donnees patient."
fi
exit "$STATUS"
