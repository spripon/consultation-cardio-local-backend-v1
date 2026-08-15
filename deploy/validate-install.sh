#!/usr/bin/env bash
# Valide l'installation. Par défaut : AUCUN démarrage de service.
#
#   bash deploy/validate-install.sh                     # validation seule
#   bash deploy/validate-install.sh --rebuild-frontend  # force npm ci && npm run build
#   bash deploy/validate-install.sh --start             # démarre puis teste health/readyz
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE_FILE=deploy/docker-compose.yml
REBUILD_FRONTEND=0
START=0

for arg in "$@"; do
  case "$arg" in
    --rebuild-frontend) REBUILD_FRONTEND=1 ;;
    --start) START=1 ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) echo "Option inconnue : $arg" >&2; exit 2 ;;
  esac
done

echo "== 1/5 Audit no-egress =="
bash scripts/verify_no_egress.sh

echo
echo "== 2/5 Frontend statique =="
if [ "$REBUILD_FRONTEND" -eq 1 ] || [ ! -f dist/index.html ]; then
  npm ci
  npm run build
else
  echo "= dist/index.html présent : build ignoré (--rebuild-frontend pour forcer)."
fi

echo
echo "== 3/5 Validation de la composition Docker =="
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  echo "! non exécuté : docker / docker compose v2 absent de cette machine."
  exit 0
fi
# `config` échoue si backend/.env ou deploy/caddy.env manque : fail-closed voulu.
docker compose -f "$COMPOSE_FILE" config >/dev/null
echo "✓ docker compose config OK (secrets non affichés)."

echo
echo "== 4/5 Build de l'image API =="
docker compose -f "$COMPOSE_FILE" build api

echo
echo "== 5/5 Démarrage =="
if [ "$START" -eq 0 ]; then
  echo "= non demandé (par défaut). Utiliser --start, ou : make up"
  echo "✓ Validation terminée sans démarrage."
  exit 0
fi

bash deploy/preflight-ubuntu.sh
docker compose -f "$COMPOSE_FILE" up -d

DOMAIN=$(grep -oE '^[A-Za-z0-9.-]+\.[A-Za-z]{2,}' deploy/Caddyfile | head -1 || true)
probe() {
  local url="$1" label="$2"
  local code
  code=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 "$url" || echo "000")
  echo "  $label -> HTTP $code"
  [ "$code" = "200" ]
}

echo "→ Attente du démarrage de l'API (30 s max)"
for _ in $(seq 1 30); do
  curl -sk -o /dev/null --max-time 3 "https://localhost/api/v1/health" && break
  sleep 1
done

STATUS=0
BASE="https://localhost"
[ -n "$DOMAIN" ] && BASE="https://$DOMAIN"
echo "Base testée : $BASE (Basic Auth attendue : 401 sans identifiants, ce qui est normal)"
probe "$BASE/api/v1/health" "health" || STATUS=1
probe "$BASE/api/v1/readyz" "readyz" || STATUS=1

if [ "$STATUS" -ne 0 ]; then
  echo "! health/readyz non 200 : soit Basic Auth (401 attendu sans identifiants),"
  echo "  soit modèle local absent (readyz 503 = fail-closed). Voir : make logs-api"
fi
echo "✓ Pile démarrée. Arrêt : make down"
