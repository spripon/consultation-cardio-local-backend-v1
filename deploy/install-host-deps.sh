#!/usr/bin/env bash
# OPTIONNEL — installe les dépendances système Ubuntu nécessaires à l'hôte.
# Idempotent (apt-get install ne réinstalle pas un paquet déjà présent).
# Aucune configuration de firewall, aucun tunnel (Cloudflare/Tailscale),
# aucun `curl | sh`, aucune suppression de paquet.
set -euo pipefail

PACKAGES=(
  docker.io
  docker-compose-plugin
  git
  curl
  python3
  python3-venv
  python3-pip
  tesseract-ocr
  tesseract-ocr-fra
  tesseract-ocr-eng
  ocrmypdf
)

cat <<INFO
== Installation des dépendances hôte (Ubuntu) ==

Paquets qui seront installés via apt-get :
$(printf '  - %s\n' "${PACKAGES[@]}")

Notes :
  * L'OCR et l'anonymisation tournent dans le conteneur API (qui embarque déjà
    tesseract). Les paquets tesseract/ocrmypdf hôte ne servent qu'aux
    vérifications et dépannages manuels.
  * Docker : ce script utilise les paquets Ubuntu (docker.io +
    docker-compose-plugin). Le dépôt officiel Docker CE est souvent plus à jour ;
    si vous le préférez, suivez la procédure officielle documentée par Docker et
    ajoutez le dépôt APT à la main (clé GPG + source APT). Ce script
    n'automatise volontairement AUCUN `curl | sh`.
  * Aucune règle ufw/iptables n'est ajoutée : ouvrez 80/443 vous-même si besoin.
  * sudo est utilisé uniquement pour apt-get.

INFO

if [ "${1:-}" != "--yes" ]; then
  read -r -p "Continuer l'installation ? [o/N] " answer
  case "$answer" in o|O|y|Y) ;; *) echo "Abandon (aucune modification)."; exit 0 ;; esac
fi

sudo apt-get update
sudo apt-get install -y --no-install-recommends "${PACKAGES[@]}"

echo
echo "✓ Paquets installés."
echo "Pour utiliser docker sans sudo :  sudo usermod -aG docker \"$USER\"  (puis rouvrir la session)"
echo "Vérifier ensuite :               bash deploy/preflight-ubuntu.sh"
