#!/usr/bin/env bash
# Prépare les fichiers de configuration locaux à partir des exemples.
# Idempotent : n'écrase JAMAIS un fichier existant.
# Ne génère aucun mot de passe, ne démarre aucun service, ne télécharge rien.
set -euo pipefail

cd "$(dirname "$0")/.."

copy_if_absent() {
  local example="$1" target="$2"
  if [ -f "$target" ]; then
    echo "= $target existe déjà : inchangé."
  elif [ -f "$example" ]; then
    cp "$example" "$target"
    chmod 600 "$target"
    echo "+ $target créé depuis $example (chmod 600) — à compléter."
  else
    echo "✗ Exemple manquant : $example" >&2
    return 1
  fi
}

copy_if_absent backend/.env.example backend/.env
copy_if_absent deploy/caddy.env.example deploy/caddy.env

cat <<'INFO'

À compléter manuellement :

1) backend/.env
   - APP_ENV=production
   - CORS_ORIGINS=https://consultation.cardiologie-tarbes.org
   - REQUIRE_OPENMED=true
   - ENABLE_SPEECH=true seulement si le modèle Whisper local est installé

2) deploy/caddy.env  (jamais committé)
   - BASIC_AUTH_USER=<identifiant>
   - BASIC_AUTH_HASH=<hash bcrypt>

   Générer le hash localement (le mot de passe en clair ne doit JAMAIS être
   écrit dans un fichier du dépôt, ni committé, ni collé dans un ticket) :

     docker run --rm -it caddy:2.8-alpine caddy hash-password
       # saisie interactive du mot de passe, sortie : $2a$14$...

   Variante non interactive (attention à l'historique du shell) :

     docker run --rm caddy:2.8-alpine caddy hash-password --plaintext 'MotDePasseFort'

Aucun service n'a été démarré. Étape suivante : deploy/download-models.sh
puis bash deploy/preflight-ubuntu.sh
INFO
