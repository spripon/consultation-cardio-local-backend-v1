#!/usr/bin/env bash
# Valide l'installation. Par défaut : AUCUN démarrage de service.
# Aucun mot de passe en clair n'est requis ; BASIC_AUTH_HASH n'est jamais lu
# ni affiché.
#
#   bash deploy/validate-install.sh            # validation seule (pas de démarrage)
#   bash deploy/validate-install.sh --start    # démarre puis valide auth + health + readyz
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE_FILE=deploy/docker-compose.yml
COMPOSE=(docker compose -f "$COMPOSE_FILE")
START=0
DOMAIN_DEFAULT=consultation.cardiologie-tarbes.org

for arg in "$@"; do
  case "$arg" in
    --start) START=1 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "Option inconnue : $arg" >&2; exit 2 ;;
  esac
done

echo "== 1/4 Audit no-egress =="
bash scripts/verify_no_egress.sh

echo
echo "== 2/4 Validation de la composition Docker =="
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  echo "✗ docker / docker compose v2 absent : validation impossible sur cette machine." >&2
  exit 1
fi
# `config` échoue si backend/.env ou deploy/caddy.env manque : fail-closed voulu.
"${COMPOSE[@]}" config >/dev/null
echo "✓ docker compose config OK (secrets non affichés)."

echo
echo "== 3/4 Construction des images (api + web) =="
# Le frontend est compilé dans l'image web : aucun Node/npm requis sur l'hôte.
"${COMPOSE[@]}" build

echo
echo "== 4/4 Démarrage et sondes =="
if [ "$START" -eq 0 ]; then
  echo "= non demandé (par défaut). Utiliser --start, ou : make up"
  echo "✓ Validation terminée sans démarrage."
  exit 0
fi

bash deploy/preflight-ubuntu.sh
"${COMPOSE[@]}" up -d

DOMAIN=$(grep -oE '^[A-Za-z0-9.-]+\.[A-Za-z]{2,}' deploy/Caddyfile | head -1 || true)
[ -n "$DOMAIN" ] || DOMAIN="$DOMAIN_DEFAULT"

STATUS=0

# A. Caddy joignable localement avec le bon Host/SNI ; SANS identifiants, une
#    réponse 401 prouve que Basic Auth est actif (fail-closed).
echo "→ Caddy : https://$DOMAIN (résolu vers 127.0.0.1), sans identifiants"
CODE=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 \
  --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/" || echo "000")
if [ "$CODE" = "401" ]; then
  echo "  ✓ Basic Auth actif (HTTP 401 sans identifiants)"
else
  echo "  ✗ attendu HTTP 401, obtenu HTTP $CODE — authentification non active ou Caddy indisponible"
  STATUS=1
fi

# B. API sondée DIRECTEMENT dans le conteneur (réseau interne, pas d'auth,
#    aucun secret, aucun contenu patient).
probe_api() {
  local path="$1"
  "${COMPOSE[@]}" exec -T api python -c "
import json, sys, urllib.request
try:
    with urllib.request.urlopen('http://127.0.0.1:8000$path', timeout=10) as r:
        print(r.status); print(r.read().decode()[:400])
except urllib.error.HTTPError as e:
    print(e.code); print(e.read().decode()[:400])
except Exception as e:
    print(0); print(type(e).__name__)
" 2>/dev/null
}

echo "→ Attente du démarrage de l'API (30 s max)"
for _ in $(seq 1 30); do
  [ "$(probe_api /api/v1/health | head -1)" = "200" ] && break
  sleep 1
done

HEALTH=$(probe_api /api/v1/health)
echo "  health -> HTTP $(echo "$HEALTH" | head -1)"
[ "$(echo "$HEALTH" | head -1)" = "200" ] || STATUS=1

READY=$(probe_api /api/v1/readyz)
READY_CODE=$(echo "$READY" | head -1)
echo "  readyz -> HTTP $READY_CODE"
if [ "$READY_CODE" != "200" ]; then
  STATUS=1
  # C. 503 = fail-closed : afficher les composants manquants (aucun contenu patient).
  MISSING=$(echo "$READY" | tail -n +2 | python3 -c "
import json, sys
try:
    print(', '.join(json.load(sys.stdin).get('missing') or []) or 'inconnu')
except Exception:
    print('réponse non exploitable')
" 2>/dev/null || echo "inconnu")
  echo "  ✗ API non prête (fail-closed). Composants manquants : $MISSING"
  echo "    Voir : make -f deploy/Makefile logs-api"
fi

echo
if [ "$STATUS" -eq 0 ]; then
  echo "✓ Validation complète : Basic Auth 401 + health 200 + readyz 200."
else
  echo "✗ Validation en échec (voir ci-dessus). La pile reste démarrée ; arrêt : make -f deploy/Makefile down"
fi
exit "$STATUS"
