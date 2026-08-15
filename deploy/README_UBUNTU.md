# Installation sur Ubuntu — commandes exactes

Cible : serveur Ubuntu 22.04 / 24.04, domaine `consultation.cardiologie-tarbes.org`.
Traitement 100 % local, aucune base de données, aucun service cloud.

---

## 1. Prérequis système

```bash
sudo apt update && sudo apt install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER" && newgrp docker

# Node.js 20 pour construire le frontend
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

## 2. Clone du dépôt

```bash
sudo mkdir -p /opt/cardio && sudo chown "$USER":"$USER" /opt/cardio
git clone <URL_DU_DEPOT> /opt/cardio/consultation
cd /opt/cardio/consultation
```

## 3. Configuration de l'environnement

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

À régler impérativement :

```env
APP_ENV=production
CORS_ORIGINS=https://consultation.cardiologie-tarbes.org
OPENMED_POLICY=gdpr_pseudonymization
OPENMED_PII_MODEL=/models/openmed-pii
REQUIRE_OPENMED=true          # fail-closed : 503 si le modèle local est absent
ALLOW_RAW_OCR_DEBUG=false     # de toute façon ignoré en production
ENABLE_SPEECH=false           # true seulement si vous déployez le modèle Whisper local
```

## 4. Téléchargement initial du modèle OpenMed (sans aucune donnée patient)

À faire **une seule fois**, avant la mise en service. C'est le seul moment où la
machine a besoin d'un accès Internet.

```bash
python3 -m venv /tmp/dlenv
/tmp/dlenv/bin/pip install huggingface_hub
/tmp/dlenv/bin/python scripts/download_openmed_model.py --out deploy/models

# Sans dictée locale :
# /tmp/dlenv/bin/python scripts/download_openmed_model.py --out deploy/models --skip-whisper

ls deploy/models/openmed-pii
```

Au runtime, le conteneur applique `HF_HUB_OFFLINE=1` et `TRANSFORMERS_OFFLINE=1` :
aucun téléchargement ne peut se déclencher pendant une requête patient.

## 5. Build du frontend

```bash
npm ci
npm run build      # génère dist/, servi en statique par Caddy
```

## 6. Tests synthétiques (données fictives uniquement)

```bash
python3 -m venv /tmp/testenv
/tmp/testenv/bin/pip install -r backend/requirements.txt
sudo apt install -y tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng
cd backend && /tmp/testenv/bin/python -m pytest -q && cd ..

# Contrôle qu'aucun appel cloud ne subsiste dans le code
bash scripts/verify_no_egress.sh
```

## 7. Lancement de la pile

Adaptez le domaine dans `deploy/Caddyfile` si nécessaire, puis :

```bash
cd deploy
docker compose up -d --build
docker compose ps
```

Le backend n'est **pas** publié sur l'hôte : il n'écoute que sur le réseau Docker
interne, en `read_only`, `cap_drop: ALL`, `no-new-privileges`, avec `/tmp` en tmpfs.
Seul Caddy expose 80/443.

## 8. DNS et pare-feu

```bash
# Enregistrement DNS A/AAAA à créer chez votre fournisseur :
#   consultation.cardiologie-tarbes.org  ->  <IP publique du serveur>
dig +short consultation.cardiologie-tarbes.org

sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Caddy obtient et renouvelle le certificat TLS automatiquement une fois le DNS propagé.

## 9. Vérification de santé

```bash
# Depuis le serveur, à travers Caddy
curl -s https://consultation.cardiologie-tarbes.org/api/v1/health | tee /dev/stderr

# Directement dans le réseau interne
docker compose exec api python -c \
  "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health').read().decode())"
```

Réponse attendue : `status: ok` avec `ocr: true`, `openmed: true` (si le modèle est en
place), `environment: production`.

## 10. Journaux

```bash
docker compose logs -f api
docker compose logs -f web
docker compose exec web tail -f /data/access.log
```

Les journaux ne contiennent **aucun contenu patient** : seulement `request_id`,
type MIME, taille et durée de traitement.

## 11. Mise à jour

```bash
cd /opt/cardio/consultation
git rev-parse HEAD > /opt/cardio/last_good_commit   # note la version actuelle
git pull
npm ci && npm run build
cd deploy && docker compose up -d --build
curl -s https://consultation.cardiologie-tarbes.org/api/v1/health
```

## 12. Rollback

```bash
cd /opt/cardio/consultation
git checkout "$(cat /opt/cardio/last_good_commit)"
npm ci && npm run build
cd deploy && docker compose up -d --build --force-recreate
curl -s https://consultation.cardiologie-tarbes.org/api/v1/health

# Arrêt complet si nécessaire
docker compose down
```

Aucune migration de base de données n'est à annuler : l'application ne persiste
aucune donnée. Un rollback se limite au code et à l'image du conteneur.

## 13. Rappels de sécurité

- L'anonymisation automatique n'est **jamais garantie** : l'interface impose une
  relecture et une confirmation explicite du soignant avant d'insérer un texte.
- Si un composant local requis manque, l'API renvoie une erreur 503 explicite.
  Aucun service externe de secours n'est appelé.
- Sauvegardez uniquement `backend/.env`, `deploy/Caddyfile` et `deploy/models/`.
## Mise à jour d'audit (durcissement)

### Modèle PII français
```bash
python scripts/download_openmed_model.py --out deploy/models
# -> deploy/models/openmed-pii-fr  (OpenMed/OpenMed-PII-French-SuperClinical-Small-44M-v1)
```
Dans `backend/.env` :
```
OPENMED_PII_MODEL=/models/openmed-pii-fr
OPENMED_LANGUAGE=fr
REQUIRE_OPENMED=true        # obligatoire en production
```
Avec `APP_ENV=production`, OpenMed est requis **même si la variable est absente** :
`/extract` et `/anonymize` renvoient 503 tant que le modèle local n'est pas monté.
Aucun téléchargement n'a lieu pendant une requête (`HF_HUB_OFFLINE=1`,
`TRANSFORMERS_OFFLINE=1`, `OPENMED_OFFLINE=1`).

### Readiness
```bash
curl -fsS http://127.0.0.1:8000/api/v1/readyz   # 503 si OCR ou modèle PII manquant
```
`/readyz` sert aussi de HEALTHCHECK Docker : un conteneur non prêt est marqué
`unhealthy` au lieu d'accepter des documents.

### Isolation réseau
Le service `api` n'est attaché qu'au réseau `backend_internal` (`internal: true`) :
Docker ne lui crée **aucune route de sortie**. Seul Caddy est sur le réseau `edge`
(ACME/HTTPS). Vérification :
```bash
docker compose exec api python -c "import socket;socket.create_connection(('1.1.1.1',443),3)"
# doit échouer (Network is unreachable)
```

### Contrôle d'accès (obligatoire si exposé sur Internet)
```bash
docker run --rm caddy:2.8-alpine caddy hash-password --plaintext '<mot-de-passe>'
cp deploy/caddy-auth/basic-auth.conf.example deploy/caddy-auth/basic-auth.conf
export BASIC_AUTH_USER=cardiologue BASIC_AUTH_HASH='$2a$14$...'
docker compose up -d web
```
Les fichiers `deploy/caddy-auth/*.conf` sont ignorés par Git. Sans fichier, Caddy
démarre sans authentification : réservé à un déploiement LAN ou Tailscale.

### Limites de documents
Un PDF de plus de `MAX_PDF_PAGES` pages est **refusé** (HTTP 413) : jamais de
compte rendu tronqué en silence.
