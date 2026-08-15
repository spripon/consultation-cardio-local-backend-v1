# Mode Cloudflare Tunnel - consultation.cardiologie-tarbes.org

Architecture cible :

```text
Internet
  -> https://consultation.cardiologie-tarbes.org
  -> Cloudflare
  -> tunnel cloudflared deja present sur le serveur Ubuntu
  -> http://127.0.0.1:8091
  -> cardio-web / Caddy :80 dans Docker
  -> frontend Vite et /api/*
  -> cardio-api / FastAPI :8000 sur reseau Docker interne
```

Le port FastAPI n'est jamais publie sur l'hote. Le seul port hote de cette application est `127.0.0.1:8091`.
Les ports hote 80/443 ne sont pas requis par cette application : le TLS public est termine par Cloudflare.

## 1. Valider l'origine locale avant Cloudflare

```bash
docker compose -f deploy/docker-compose.yml up -d --build
curl -sS -o /dev/null -w 'HTTP=%{http_code}\n' http://127.0.0.1:8091/
```

Attendu sans credentials : `HTTP=401`.

## 2. Utiliser le tunnel existant

Le serveur publie deja `planning.cardiologie-tarbes.org`. Ne creer un nouveau tunnel que si cela est volontaire : un meme Cloudflare Tunnel peut publier plusieurs applications.

### Methode recommandee : tunnel gere depuis le Dashboard

Dans Cloudflare Dashboard :

1. `Networking` -> `Tunnels`.
2. Ouvrir le tunnel deja utilise par `planning.cardiologie-tarbes.org`.
3. Onglet `Routes` -> `Add route` -> `Published application`.
4. Hostname : `consultation.cardiologie-tarbes.org`.
5. Service URL : `http://localhost:8091` (equivalent a `http://127.0.0.1:8091` puisque cloudflared tourne sur la meme machine).
6. Enregistrer.

Cloudflare cree/associe le routage DNS du hostname au tunnel dans une zone DNS geree par Cloudflare.

### Alternative : tunnel gere par /etc/cloudflared/config.yml

Avant toute modification :

```bash
sudo cp /etc/cloudflared/config.yml \
  /etc/cloudflared/config.yml.backup-$(date +%Y%m%d-%H%M%S)
```

Ajouter la seconde regle AVANT la regle catch-all finale :

```yaml
ingress:
  - hostname: planning.cardiologie-tarbes.org
    service: http://localhost:<PORT_PLANNING_EXISTANT>

  - hostname: consultation.cardiologie-tarbes.org
    service: http://localhost:8091

  - service: http_status:404
```

Ne pas modifier la regle planning existante. La regle `http_status:404` doit rester la derniere regle.

Valider avant restart :

```bash
sudo cloudflared tunnel --config /etc/cloudflared/config.yml ingress validate
```

Puis seulement si la validation est OK :

```bash
sudo systemctl restart cloudflared
sudo systemctl status cloudflared --no-pager
```

Selon le type de tunnel/configuration, le DNS peut etre gere depuis le Dashboard ou par `cloudflared tunnel route dns <TUNNEL> consultation.cardiologie-tarbes.org`. Ne pas executer cette commande sans avoir identifie le tunnel existant et le mode de gestion actuel.

## 3. Verification non destructive

```bash
bash deploy/validate-cloudflare-tunnel.sh
```

Le script exige :

- `cloudflared` present ;
- origine locale `http://127.0.0.1:8091` -> HTTP 401 ;
- listener 8091 lie uniquement a `127.0.0.1` ;
- resolution DNS du sous-domaine ;
- URL publique `https://consultation.cardiologie-tarbes.org` -> HTTP 401 sans credentials.

Un `502` public indique typiquement que Cloudflare/tunnel est joignable mais que `cloudflared` ne peut pas atteindre l'origine locale configuree. Tester alors `curl http://127.0.0.1:8091` et verifier le Service URL.

## 4. Notes de securite

- Le trafic utilisateur passe par le reseau Cloudflare avant d'atteindre `cloudflared`.
- Le backend FastAPI reste local et sans egress Internet au runtime.
- Le frontend n'est pas publie sur `0.0.0.0` ni sur l'IP Tailscale : uniquement `127.0.0.1:8091`.
- Basic Auth reste obligatoire dans Caddy. Cloudflare Access pourra eventuellement ajouter une seconde couche d'authentification plus tard.
- Aucune donnee patient reelle ne doit etre utilisee avant validation DSI/DPO/etablissement et validation technique complete.

Documentation Cloudflare de reference :
- https://developers.cloudflare.com/tunnel/setup/
- https://developers.cloudflare.com/tunnel/routing/
- https://developers.cloudflare.com/tunnel/advanced/local-management/configuration-file/
