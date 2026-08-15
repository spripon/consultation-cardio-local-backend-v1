# Déploiement auto-hébergé sur Ubuntu

Cette application est conçue pour tourner **entièrement sur votre propre serveur**.
Aucune donnée patient (image, PDF, texte, audio) ne sort de la machine : il n'existe
aucun appel vers un service d'IA externe dans le code (`scripts/verify_no_egress.sh`
le vérifie automatiquement).

## 1. Prérequis

- Ubuntu 22.04 ou 24.04
- Docker Engine + plugin Compose
- 4 Go de RAM minimum (8 Go recommandés si la dictée locale est activée)
- Un nom de domaine interne pointant vers le serveur (pour le HTTPS automatique)

## 2. Récupération des modèles locaux (une seule fois)

Les modèles sont téléchargés **avant** le déploiement, sur une machine ayant accès à
Internet. Le conteneur applicatif tourne ensuite hors ligne (`HF_HUB_OFFLINE=1`).

```bash
pip install huggingface_hub
python scripts/download_models.py --out deploy/models
```

Si vous n'utilisez ni la détection PII par modèle ni la dictée :

```bash
python scripts/download_models.py --skip-pii --skip-whisper
```

## 3. Configuration

```bash
cp backend/.env.example backend/.env
```

Variables importantes :

| Variable | Rôle |
| --- | --- |
| `APP_ENV` | `production` verrouille le mode debug OCR et désactive `/docs` |
| `CORS_ORIGINS` | origine du frontend ; jamais `*` en production |
| `OPENMED_POLICY` | `gdpr_pseudonymization` (défaut cardio) ou `strict_no_leak` |
| `OPENMED_PII_MODEL` | chemin local du modèle PII, ex. `/models/openmed-pii` |
| `REQUIRE_OPENMED` | `true` = erreur 503 explicite si le modèle local manque (fail-closed) |
| `ENABLE_SPEECH` | `true` pour activer la dictée locale (faster-whisper) |
| `ALLOW_RAW_OCR_DEBUG` | ignoré si `APP_ENV=production` |

## 4. Build du frontend

```bash
npm ci
npm run build      # produit dist/, servi en statique par Caddy
```

## 5. Lancement de la pile

Adaptez le domaine dans `deploy/Caddyfile`, puis :

```bash
cd deploy
docker compose up -d --build
docker compose ps
curl -s https://votre-domaine/api/v1/health
```

Seul Caddy expose les ports 80/443. L'API FastAPI n'est joignable que sur le réseau
interne Docker ; elle écoute `0.0.0.0:8000` **à l'intérieur du conteneur uniquement**.

## 6. Vérifications après déploiement

```bash
# Aucun appel cloud dans le code
bash scripts/verify_no_egress.sh

# Tests d'anonymisation et de catégorisation (données synthétiques uniquement)
cd backend && pytest -q
```

Le point `/api/v1/health` indique la disponibilité réelle de chaque composant local
(`ocr`, `openmed`, `speech`) sans révéler de chemin ni de secret.

## 7. Isolement réseau (recommandé)

Pour garantir techniquement l'absence de fuite, coupez l'egress du conteneur API
après le premier build :

```bash
sudo ufw default deny outgoing
sudo ufw allow in 443/tcp
sudo ufw allow in 80/tcp
sudo ufw enable
```

Le conteneur `api` n'a besoin d'aucun accès sortant au runtime.

## 8. Sauvegardes

Il n'y a **aucune base de données** : les documents traités ne sont jamais persistés
(traitement en mémoire + `tmpfs` effacé à l'arrêt). Sauvegardez uniquement
`backend/.env`, `deploy/Caddyfile` et `deploy/models/`.

## 9. Limites à connaître

- L'anonymisation automatique **n'est pas garantie**. L'interface impose une
  relecture et une confirmation humaine avant toute insertion dans le formulaire.
- L'OCR d'un document manuscrit ou de mauvaise qualité peut être partiel : le score
  de confiance OCR est affiché à l'utilisateur.
- Si un composant local requis est absent, l'API renvoie une erreur 503 explicite.
  Aucun service externe de secours n'est appelé.