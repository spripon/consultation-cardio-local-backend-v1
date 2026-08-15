#!/usr/bin/env bash
# Validation non destructive du chemin public Cloudflare Tunnel.
# Ne modifie ni DNS, ni tunnel, ni service cloudflared.
set -euo pipefail

DOMAIN="consultation.cardiologie-tarbes.org"
LOCAL_ORIGIN="http://127.0.0.1:8091"
STATUS=0

ok()   { echo "OK  $*"; }
fail() { echo "ERR $*"; STATUS=1; }
warn() { echo "WARN $*"; }

echo "== Validation Cloudflare Tunnel =="
echo "Public : https://$DOMAIN"
echo "Local  : $LOCAL_ORIGIN"
echo

if command -v cloudflared >/dev/null 2>&1; then
  ok "cloudflared present : $(cloudflared --version 2>/dev/null | head -1)"
else
  fail "cloudflared absent du PATH"
fi

if command -v systemctl >/dev/null 2>&1; then
  if systemctl is-active --quiet cloudflared 2>/dev/null; then
    ok "service cloudflared actif"
  else
    warn "service cloudflared non actif ou lance autrement"
  fi
fi

LOCAL_CODE=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "$LOCAL_ORIGIN/" || echo "000")
if [ "$LOCAL_CODE" = "401" ]; then
  ok "origine locale repond 401 sans identifiants"
else
  fail "origine locale : attendu 401, obtenu $LOCAL_CODE"
fi

if command -v ss >/dev/null 2>&1; then
  LISTEN=$(ss -ltnH 2>/dev/null | awk '$4 ~ /:8091$/ {print $4}' | head -1 || true)
  case "$LISTEN" in
    127.0.0.1:8091) ok "8091 lie a 127.0.0.1 uniquement" ;;
    "") fail "aucun listener sur 8091" ;;
    *) fail "listener 8091 inattendu : $LISTEN" ;;
  esac
fi

if command -v dig >/dev/null 2>&1; then
  DNS=$(dig +short "$DOMAIN" A | paste -sd, -)
  [ -n "$DNS" ] && ok "DNS public resolu : $DNS" || warn "aucune reponse A via dig"
else
  getent ahostsv4 "$DOMAIN" >/dev/null 2>&1 && ok "DNS public resolu" || warn "resolution DNS non confirmee"
fi

# Le test public doit passer par Cloudflare et revenir 401 du Basic Auth Caddy.
PUBLIC_CODE=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "https://$DOMAIN/" || echo "000")
if [ "$PUBLIC_CODE" = "401" ]; then
  ok "chemin public Cloudflare -> tunnel -> localhost:8091 -> Caddy : HTTP 401"
else
  fail "chemin public : attendu 401, obtenu $PUBLIC_CODE"
fi

if [ "$STATUS" -eq 0 ]; then
  echo
  echo "OK Validation Cloudflare Tunnel reussie."
else
  echo
  echo "ERR Validation Cloudflare Tunnel incomplete. Ne pas utiliser de donnees patient reelles."
fi
exit "$STATUS"
