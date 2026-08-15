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
```

Le script installe `docker.io`, `docker-compose-plugin`, `git`, `curl`,
`python3`, `tesseract-ocr(+fra,+eng)`, `ocrmypdf`. Il n'ajoute **aucune** règle
de firewall, aucun tunnel, aucun `curl | sh`. Si vous préférez Docker CE du
dépôt officiel Docker, ajoutez ce dépôt APT manuellement (clé GPG + source),
puis passez cette étape.

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

Les poids vont dans `deploy/models/` (ignoré par Git) et sont montés en lecture
seule sous `/models` dans le conteneur. Après cette étape, le runtime est de
nouveau strictement hors ligne (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`) et
aucun téléchargement n'est possible pendant un traitement.

## 5. Construire

```bash
make -f deploy/Makefile build     # npm ci && npm run build, puis image API
```

## 6. Vérifier puis démarrer

```bash
make -f deploy/Makefile preflight   # lecture seule : rien n'est modifié
make -f deploy/Makefile validate    # no-egress + compose config + build API
make -f deploy/Makefile up          # dépend de preflight
```

`validate-install.sh --start` démarre puis interroge `/api/v1/health` et
`/api/v1/readyz`. Un `401` sans identifiants est normal (Basic Auth) ; un `503`
sur `readyz` signifie qu'un composant local requis manque — comportement
fail-closed attendu.

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
make -f deploy/Makefile build
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
