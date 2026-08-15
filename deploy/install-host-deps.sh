#!/usr/bin/env bash
# OPTIONNEL — installe les dépendances système Ubuntu nécessaires à l'hôte.
# Idempotent. Ne DÉSINSTALLE jamais un paquet Docker existant, ne configure
# aucun firewall, aucun tunnel (Cloudflare/Tailscale), aucun `curl | sh`.
set -euo pipefail

BASE_PACKAGES=(
  git
  curl
  ca-certificates
  python3
  python3-venv
  python3-pip
)

cat <<INFO
== Installation des dépendances hôte (Ubuntu) ==

Paquets de base installés via apt-get :
$(printf '  - %s\n' "${BASE_PACKAGES[@]}")

Docker : traité séparément ci-dessous.
  * Si `docker compose version` fonctionne déjà, Docker n'est PAS touché.
  * Sinon, le script choisit le paquet Compose v2 réellement disponible :
      - dépôts Ubuntu        -> docker.io + docker-compose-v2
      - dépôt Docker officiel -> docker-ce + docker-compose-plugin
  * Si aucun Compose v2 n'est disponible, le script s'arrête avec les
    instructions vers la procédure officielle Docker CE (ajout manuel du dépôt
    APT : clé GPG + source), sans `curl | sh`.

Node/npm ne sont PAS nécessaires : le frontend est compilé dans l'image Docker
web (deploy/Dockerfile.web).

Tesseract/ocrmypdf ne sont PAS installés sur l'hôte : ils sont embarqués dans
l'image API. sudo est utilisé uniquement pour apt-get.

INFO

if [ "${1:-}" != "--yes" ]; then
  read -r -p "Continuer l'installation ? [o/N] " answer
  case "$answer" in o|O|y|Y) ;; *) echo "Abandon (aucune modification)."; exit 0 ;; esac
fi

sudo apt-get update
sudo apt-get install -y --no-install-recommends "${BASE_PACKAGES[@]}"

apt_has() { apt-cache show "$1" >/dev/null 2>&1; }

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  echo "= Docker + Compose v2 déjà fonctionnels : aucun paquet Docker modifié."
  echo "  $(docker compose version | head -1)"
elif apt_has docker-compose-v2; then
  echo "→ Compose v2 depuis les dépôts Ubuntu : docker.io + docker-compose-v2"
  sudo apt-get install -y --no-install-recommends docker.io docker-compose-v2
elif apt_has docker-compose-plugin; then
  echo "→ Compose v2 depuis le dépôt Docker officiel : docker-ce + docker-compose-plugin"
  if apt_has docker-ce; then
    sudo apt-get install -y --no-install-recommends docker-ce docker-ce-cli containerd.io docker-compose-plugin
  else
    sudo apt-get install -y --no-install-recommends docker.io docker-compose-plugin
  fi
else
  cat <<'ERR' >&2

✗ Aucun paquet Docker Compose v2 disponible dans les dépôts APT configurés.

Ajoutez le dépôt Docker CE officiel MANUELLEMENT (documentation Docker :
« Install Docker Engine on Ubuntu », section « Install using the apt
repository ») : installation de la clé GPG dans /etc/apt/keyrings, ajout de la
source dans /etc/apt/sources.list.d/docker.list, puis `sudo apt-get update` et
`sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin`.

Ce script n'automatise volontairement aucun script d'installation distant.
ERR
  exit 1
fi

echo
echo "✓ Dépendances hôte installées."
echo "Pour utiliser docker sans sudo :  sudo usermod -aG docker \"$USER\"  (puis rouvrir la session)"
echo "Vérifier :                        docker compose version && bash deploy/preflight-ubuntu.sh"
