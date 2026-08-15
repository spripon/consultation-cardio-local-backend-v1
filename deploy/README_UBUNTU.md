# Installation reproductible sur Ubuntu (CPU-only, 100 % local)

Guide pas-à-pas pour héberger l'application sur un serveur Ubuntu que vous
contrôlez. **Aucune donnée patient ne sort du serveur** : OCR, anonymisation PII
et catégorisation sont exécutées localement dans un conteneur sans accès Internet.

> Avertissement : avant tout traitement de données patients réelles, une
> validation DSI / DPO / établissement est **obligatoire** (analyse d'impact,
> registre des traitements, hébergement). L'anonymisation automatique n'est pas
> garantie : la relecture humaine reste obligatoire dans l'interface.

Baseline auditée : voir [`docs/BASELINE.md`](../docs/BASELINE.md).

## 0. Prérequis matériels

- Ubuntu 22.04 / 24.04 LTS, x86_64 ou aarch64, **CPU uniquement**
- 8 Go de RAM recommandés (4 Go minimum), 15 Go de disque libre
- Ports 80 et 443 libres, accessibles depuis Internet si domaine public

## 1. Dépendances hôte (optionnel mais recommandé)

```bash
bash deploy/install-host-deps.sh        # demande confirmation avant apt-get
sudo usermod -aG docker "$USER"          # puis rouvrir la session
docker compose version                   # doit fonctionner
```

Le script installe `git`, `curl`, `ca-certificates`, `python3`, `python3-venv`,
`python3-pip`, puis un Docker avec **Compose v2** :

- si `docker compose version` fonctionne déjà, Docker n'est pas touché ;
- sinon, `docker.io` + `docker-compose-v2` (paquets **Ubuntu**) ;
- sinon `docker-ce` + `docker-compose-plugin` (paquets du **dépôt Docker
  officiel**, s'il est déjà configuré) ;
- sinon le script s'arrête et renvoie vers la procédure officielle Docker CE
  (ajout manuel du dépôt APT : clé GPG + source). Aucun `curl | sh`.

Aucun paquet Docker existant n'est désinstallé, aucune règle de firewall n'est
ajoutée, aucun tunnel n'est configuré.

**Node/npm ne sont pas nécessaires sur l'hôte** : le frontend est compilé dans
l'image Docker `web` (`deploy/Dockerfile.web`, étape builder `node:22-alpine`).
Tesseract et ocrmypdf sont embarqués dans l'image API.

## 2. Cloner le dépôt

```bash
git clone https://github.com/spripon/consultation-cardio-local-backend-v1.git
cd consultation-cardio-local-backend-v1
git checkout main
```

(Le nom `spripon/consultation-cardio-local-backend-v1` est un placeholder tant
que le dépôt privé n'a pas été créé depuis Lovable.)

## 3. Configuration locale

```bash
make -f deploy/Makefile prepare-config
```

Crée `backend/.env` et `deploy/caddy.env` depuis les exemples (jamais écrasés,
`chmod 600`). Ces deux fichiers sont **obligatoires** et **jamais committés**.

Puis éditez `backend/.env` :

```
APP_ENV=production
CORS_ORIGINS=https://consultation.cardiologie-tarbes.org
REQUIRE_OPENMED=true
ALLOW_RAW_OCR_DEBUG=false
ENABLE_SPEECH=false          # true seulement si le modèle Whisper est installé
```

### Basic Auth (obligatoire, fail-closed)

Générez un hash bcrypt **localement** :

```bash
docker run --rm -it caddy:2.8-alpine caddy hash-password
```

Reportez la sortie dans `deploy/caddy.env` :

```
BASIC_AUTH_USER=cardio
BASIC_AUTH_HASH=$2a$14$...
```

Le mot de passe en clair ne doit jamais être écrit dans un fichier du dépôt,
committé, ni transmis par messagerie. Si `deploy/caddy.env` est absent,
`docker compose up` **échoue** : le site public ne peut pas démarrer sans
authentification.

## 4. Télécharger les modèles (phase installation, avec réseau)

```bash
make -f deploy/Makefile models          # modèle PII français OpenMed 2.0
make -f deploy/Makefile models-speech   # + faster-whisper small (si dictée)
```

Le script crée un venv d'installation dédié `deploy/.venv-models` (Ubuntu récent
refuse `pip install --user`, PEP 668) et y installe `huggingface_hub`. Aucun
jeton Hugging Face n'est nécessaire : les modèles sont publics.

Les poids vont dans `deploy/models/` (ignoré par Git) et sont montés en lecture
seule sous `/models` dans le conteneur. Après cette étape, le runtime est de
nouveau strictement hors ligne (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`) et
aucun téléchargement n'est possible pendant un traitement.

## 5. Construire les images

```bash
make -f deploy/Makefile build     # docker compose build : web (frontend) + api
```

Le frontend est compilé dans l'image `web` ; rien n'est construit sur l'hôte et
aucun répertoire `dist/` hôte n'est utilisé. Le contexte de build est filtré par
le `.dockerignore` racine : ni `backend/.env`, ni `deploy/caddy.env`, ni
`deploy/models/` n'entrent dans une image.

## 6. Vérifier puis démarrer

```bash
make -f deploy/Makefile preflight   # lecture seule : rien n'est modifié
make -f deploy/Makefile validate    # no-egress + compose config + build API
make -f deploy/Makefile up          # dépend de preflight
```

`bash deploy/validate-install.sh --start` démarre la pile puis valide, sans
jamais lire ni afficher `BASIC_AUTH_HASH` et sans mot de passe en clair :

1. Caddy interrogé localement avec le bon Host/SNI
   (`curl --resolve consultation.cardiologie-tarbes.org:443:127.0.0.1`) : un
   **HTTP 401** sans identifiants prouve que Basic Auth est actif ;
2. `/api/v1/health` et `/api/v1/readyz` sondés **directement dans le conteneur
   API** (`docker compose exec -T api`), qui doivent répondre **200** ;
3. si `readyz` renvoie 503, le script sort en code non nul et affiche les
   composants `missing` (fail-closed, aucun contenu patient).

Le script ne sort en 0 que si les trois contrôles passent.

Le préflight tolère les ports 80/443 occupés **par le conteneur attendu
`cardio-web` déjà démarré** : `make up` reste donc idempotent sur une pile en
cours d'exécution. Tout autre occupant du port fait échouer le préflight.

## 7. DNS pour `consultation.cardiologie-tarbes.org`

- Enregistrement `A` → adresse IPv4 publique du serveur (et `AAAA` si IPv6).
- Aucun proxy tiers : le trafic doit arriver **directement** sur Caddy, qui
  obtient le certificat TLS via ACME/Let's Encrypt.
- **Exigence « aucun contenu patient via un tiers » : n'utilisez pas Cloudflare
  Tunnel, ni le proxy orange de Cloudflare, ni un reverse proxy externe.** Ces
  services déchiffrent le trafic et verraient donc le contenu transmis. DNS
  direct + Caddy uniquement.
- Ports 80 (ACME) et 443 doivent être joignables depuis Internet.

## 8. Vérification no-egress

Depuis le dépôt :

```bash
bash scripts/verify_no_egress.sh
```

Depuis le conteneur API (doit échouer : réseau Docker `internal: true`, donc
aucune route de sortie) :

```bash
docker compose -f deploy/docker-compose.yml exec api python -c \
  "import socket; socket.create_connection(('1.1.1.1', 443), timeout=5)"
# attendu : OSError / timeout

docker compose -f deploy/docker-compose.yml exec api python -c \
  "import socket; print(socket.gethostbyname('example.com'))"
# attendu : échec de résolution
```

## 9. Sauvegarde et rollback

- Notez **le SHA GitHub déployé** : `git rev-parse HEAD` (à conserver hors
  serveur, avec la date de mise en production).
- Sauvegardez `backend/.env` et `deploy/caddy.env` hors dépôt, en coffre-fort.
  `deploy/models/` peut être re-téléchargé, pas besoin de le sauvegarder.
- Rollback :

```bash
make -f deploy/Makefile down
git checkout <sha-github-precedent>
make -f deploy/Makefile build      # reconstruit web + api depuis ce SHA
make -f deploy/Makefile up
```

## 10. Mises à jour

Jamais d'auto-update. Après revue et validation d'une nouvelle version :

```bash
git fetch origin && git log --oneline HEAD..origin/main   # revue
git checkout main && git pull
make -f deploy/Makefile build validate up
```

## 11. Arrêt d'urgence

```bash
docker compose -f deploy/docker-compose.yml down
```

Le service est immédiatement injoignable. Les fichiers temporaires OCR vivent en
`tmpfs` et disparaissent à l'arrêt du conteneur ; les volumes Caddy (certificats)
sont conservés.
