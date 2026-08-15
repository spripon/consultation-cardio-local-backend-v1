# Installation Ubuntu - mode Cloudflare Tunnel

Architecture cible : `consultation.cardiologie-tarbes.org` est publie par le Cloudflare Tunnel deja utilise sur ce serveur, notamment pour `planning.cardiologie-tarbes.org`. Le nouveau service local est `http://127.0.0.1:8091`.

```text
Internet HTTPS
  -> Cloudflare
  -> cloudflared sur l'hote Ubuntu
  -> http://127.0.0.1:8091
  -> cardio-web / Caddy :80
  -> frontend + /api/*
  -> cardio-api / FastAPI :8000 (Docker interne uniquement)
```

Le backend n'a aucun port hote publie. Le frontend n'est pas lie a l'IP Tailscale ni a `0.0.0.0`, uniquement a `127.0.0.1:8091`. Les ports 80/443 de l'hote ne sont pas necessaires pour cette application.

> Avant toute donnee patient reelle : validation DSI/DPO/etablissement, validation de l'hebergement et de la securite. Les tests d'installation sont exclusivement synthetiques.

## 1. Cloner la release stable

```bash
sudo mkdir -p /opt/consultation-cardio-local-backend-v1
sudo chown "$USER":"$USER" /opt/consultation-cardio-local-backend-v1

git clone --branch release/ubuntu-v1 --single-branch \
  https://github.com/spripon/consultation-cardio-local-backend-v1.git \
  /opt/consultation-cardio-local-backend-v1

cd /opt/consultation-cardio-local-backend-v1
git rev-parse HEAD
```

Conserver le SHA deploye dans le manifeste local.

## 2. Inventaire avant modification

```bash
docker --version || true
docker compose version || true
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' || true
ss -ltnp 2>/dev/null | grep -E ':(8091|80|443)\b' || true
cloudflared --version || true
systemctl is-active cloudflared 2>/dev/null || true
```

Ne jamais arreter automatiquement un autre service. Un conflit sur 8091 doit etre signale ; ne pas tuer le processus existant.

## 3. Dependances hote

```bash
bash deploy/install-host-deps.sh --yes
sudo systemctl enable --now docker
docker compose version
docker info
```

Si l'utilisateur n'a pas acces a Docker : `sudo usermod -aG docker "$USER"`, puis nouvelle session si necessaire.

## 4. Configuration locale

```bash
make -f deploy/Makefile prepare-config
chmod 600 backend/.env deploy/caddy.env
```

Valeurs importantes dans `backend/.env` :

```env
APP_ENV=production
CORS_ORIGINS=https://consultation.cardiologie-tarbes.org
OPENMED_POLICY=gdpr_pseudonymization
OPENMED_PII_MODEL=/models/openmed-pii-fr
OPENMED_LANGUAGE=fr
REQUIRE_OPENMED=true
HF_HUB_OFFLINE=true
OPENMED_OFFLINE=true
ALLOW_RAW_OCR_DEBUG=false
ENABLE_SPEECH=false
```

Generer le Basic Auth localement. Le hash bcrypt doit etre single-quoted :

```env
BASIC_AUTH_USER=cardio
BASIC_AUTH_HASH='$2a$14$...'
```

Ne jamais committer `backend/.env`, `deploy/caddy.env`, mots de passe ou modeles.

## 5. Modele OpenMed local

```bash
make -f deploy/Makefile models
test -n "$(ls -A deploy/models/openmed-pii-fr)"
```

Le telechargement Hugging Face est une phase d'installation sans donnee patient. Le runtime API reste offline.

## 6. Build et validation locale

```bash
bash scripts/verify_no_egress.sh
make -f deploy/Makefile build
make -f deploy/Makefile preflight
bash deploy/validate-install.sh --start
```

La validation locale exige :

- `http://127.0.0.1:8091/` -> HTTP 401 sans credentials ;
- listener 8091 uniquement sur `127.0.0.1` ;
- `/api/v1/health` -> 200 ;
- `/api/v1/readyz` -> 200 ;
- connexion TCP sortante du conteneur API impossible.

Tesseract :

```bash
docker compose -f deploy/docker-compose.yml exec -T api tesseract --list-langs
```

`fra` et `eng` doivent etre presents.

## 7. Ajouter le hostname au Cloudflare Tunnel existant

Voir `deploy/CLOUDFLARE_TUNNEL.md`.

### Tunnel gere dans le Dashboard Cloudflare

Dans `Networking -> Tunnels`, ouvrir le tunnel existant qui publie deja `planning.cardiologie-tarbes.org`, puis :

1. `Routes` -> `Add route` -> `Published application`.
2. Hostname : `consultation.cardiologie-tarbes.org`.
3. Service URL : `http://localhost:8091`.
4. Enregistrer.

Un meme tunnel peut publier plusieurs applications ; il n'est pas necessaire de creer un second tunnel.

### Tunnel gere par /etc/cloudflared/config.yml

Sauvegarder avant modification :

```bash
sudo cp /etc/cloudflared/config.yml \
  /etc/cloudflared/config.yml.backup-$(date +%Y%m%d-%H%M%S)
```

Ajouter avant le catch-all final :

```yaml
- hostname: consultation.cardiologie-tarbes.org
  service: http://localhost:8091
```

Conserver la route planning existante et la regle finale :

```yaml
- service: http_status:404
```

Valider :

```bash
sudo cloudflared tunnel --config /etc/cloudflared/config.yml ingress validate
```

Puis seulement si OK :

```bash
sudo systemctl restart cloudflared
sudo systemctl status cloudflared --no-pager
```

Ne pas executer `cloudflared tunnel route dns` tant que le mode de gestion du tunnel existant et son identifiant n'ont pas ete confirmes.

## 8. Valider le chemin public

```bash
bash deploy/validate-cloudflare-tunnel.sh
```

Attendu :

- cloudflared present ;
- origine locale 401 ;
- 8091 sur loopback uniquement ;
- DNS resolu ;
- `https://consultation.cardiologie-tarbes.org/` -> HTTP 401 sans credentials.

Si le public renvoie 502, verifier d'abord :

```bash
curl -I http://127.0.0.1:8091
```

Si le local fonctionne mais le public est 502, verifier la Service URL du Published application et les logs cloudflared.

## 9. Tests synthetiques PII/categorisation

Avant toute donnee reelle, tester `/api/v1/anonymize` et `/api/v1/categorize` avec des identites entierement fictives. `safeToInject` doit etre `true` apres suppression des identifiants synthetiques.

## 10. Manifeste local

```bash
sudo mkdir -p /var/lib/consultation-cardio
sudo sh -c '{
  echo "deployed_at=$(date -Is)"
  echo "repo=https://github.com/spripon/consultation-cardio-local-backend-v1.git"
  echo "branch=release/ubuntu-v1"
  echo "git_sha=$(git -C /opt/consultation-cardio-local-backend-v1 rev-parse HEAD)"
  echo "baseline_sha=de542fee77a69ee355d920b33b80f0387148f059"
} > /var/lib/consultation-cardio/deployment-manifest.txt'
sudo chmod 600 /var/lib/consultation-cardio/deployment-manifest.txt
```

## 11. Arret / rollback

Arreter uniquement cette pile :

```bash
docker compose -f deploy/docker-compose.yml down
```

Ne jamais utiliser `docker system prune`, `docker volume prune` ou une commande globale susceptible d'affecter Hermes/DeepECG/autres conteneurs.

Rollback code :

```bash
git checkout <SHA_PRECEDENT_VALIDE>
make -f deploy/Makefile build
make -f deploy/Makefile up
```

## 12. Dictee locale ulterieure

Apres validation de la V1 OCR/PII :

```bash
make -f deploy/Makefile models-speech
```

Puis `ENABLE_SPEECH=true` dans `backend/.env` et rebuild API. Tester uniquement avec audio synthetique d'abord.

## 13. Documentation officielle Cloudflare

- https://developers.cloudflare.com/tunnel/setup/
- https://developers.cloudflare.com/tunnel/routing/
- https://developers.cloudflare.com/tunnel/advanced/local-management/configuration-file/

Cloudflare Tunnel etablit des connexions sortantes de `cloudflared` vers le reseau Cloudflare ; aucun port entrant 80/443 n'est requis pour l'origine locale dans cette architecture.
