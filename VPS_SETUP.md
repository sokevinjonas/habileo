# 🖥️ Deploiement Habileo sur le VPS — Journal

Ce document decrit les etapes **reellement executees** pour mettre le backend Habileo en production sur le VPS, depuis zero jusqu'au HTTPS fonctionnel.

Sert de reference pour :

- Comprendre la config actuelle
- Refaire le setup sur un autre VPS (dev/staging)
- Debuguer si quelque chose casse

---

## 📋 Informations de la prod

| | Valeur |
| --- | --- |
| **VPS IPv4** | `72.61.98.7` |
| **Utilisateur SSH** | `admin@srv1096720` |
| **Chemin du projet** | `~/projects/habileo/` |
| **Domaine public** | `https://api-habileo.couturart.app` |
| **Provider DNS** | Hostinger (nameservers `ns1.dns-parking.com`, `ns2.dns-parking.com`) |
| **Reverse proxy** | nginx (natif sur le host, pas Docker) |
| **HTTPS** | Let's Encrypt via certbot (auto-renew) |
| **Image Docker** | `sokevinjonas/habileo-backend:v1.1.2` |
| **Port interne** | `127.0.0.1:5100` (pas 5000, deja pris) |

---

## 🏛️ Architecture

```text
                            Internet
                                │
                                ▼
                         ┌──────────────┐
                         │ api-habileo  │   DNS A record
                         │ .couturart   │   → 72.61.98.7
                         │ .app         │
                         └──────┬───────┘
                                │ HTTPS 443 / HTTP 80
                                ▼
                         ┌──────────────┐
                         │ nginx (host) │   Reverse proxy + SSL
                         │              │   Let's Encrypt cert
                         │  sites-      │
                         │  enabled/    │
                         └──────┬───────┘
                                │ proxy_pass http://127.0.0.1:5100
                                ▼
                         ┌──────────────┐
                         │ habileo-     │   Docker container
                         │ backend      │   (image Docker Hub)
                         │ (Gunicorn)   │   v1.1.2
                         └──────┬───────┘
                                │
                  ┌─────────────┴─────────────┐
                  ▼                           ▼
           Cloudinary                   Replicate
           (images)                  (modeles IA)
```

---

## 🚀 Etape 1 — Preparation locale (machine de dev)

### 1.1 Build + push de l'image Docker

```bash
cd ~/Bureau/Projet-IA/habileo
./deploy.sh v1.1.2
```

Ce script :

- Build `habileo-backend` et `habileo-frontend` avec les derniers changements
- Tag les images `sokevinjonas/habileo-{backend,frontend}:v1.1.2` + `latest`
- Push sur Docker Hub

### 1.2 Config frontend pour la prod

[`front/src/environments/environment.prod.ts`](front/src/environments/environment.prod.ts) :

```typescript
export const environment = {
  production: true,
  apiUrl: 'https://api-habileo.couturart.app',
  admob: {
    bannerId: 'ca-app-pub-6229155547551594/6404925159',
    interstitialId: 'ca-app-pub-6229155547551594/1305687894',
  },
};
```

Ce fichier est utilise quand tu builds l'APK pour publication Play Store.

---

## 🚀 Etape 2 — Setup sur le VPS

### 2.1 Creation de l'arborescence

```bash
ssh admin@srv1096720
mkdir -p ~/projects/habileo
cd ~/projects/habileo
```

### 2.2 `docker-compose.yml`

```bash
nano docker-compose.yml
```

Contenu :

```yaml
services:
  backend:
    image: sokevinjonas/habileo-backend:v1.1.2
    container_name: habileo-backend
    restart: unless-stopped
    ports:
      - "127.0.0.1:5100:5000"
    env_file:
      - ./backend.env
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

**⚠️ Note importante sur le port** : on bind sur `127.0.0.1:5100` au lieu de `5000` parce que le port 5000 est deja pris par un autre service sur le VPS. Le port interne du conteneur reste 5000, c'est le port expose vers l'hote qui change.

### 2.3 `backend.env`

```bash
nano backend.env
```

Contenu (remplacer par tes vraies cles) :

```env
# Flask
FLASK_DEBUG=0
SECRET_KEY=<generer avec: openssl rand -hex 32>
PORT=5000

# Replicate
REPLICATE_API_TOKEN=r8_...
REPLICATE_MODEL_VERSION=0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985
REPLICATE_POLL_INTERVAL=2
REPLICATE_TIMEOUT=180

# Cloudinary
CLOUDINARY_URL=cloudinary://...
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

# Uploads
MAX_UPLOAD_MB=10
```

Proteger le fichier :

```bash
chmod 600 backend.env
```

### 2.4 Pull + lancement

```bash
docker compose pull
docker compose up -d
docker compose ps
```

Attendu :

```text
NAME              STATUS                  PORTS
habileo-backend   Up (healthy)            127.0.0.1:5100->5000/tcp
```

### 2.5 Test local

```bash
curl http://localhost:5100/api/health
# → {"status":"ok"}
```

---

## 🌐 Etape 3 — DNS

### 3.1 Chez Hostinger (ou ton registrar)

Dans la zone DNS de `couturart.app`, ajouter :

```text
Type: A
Nom:  api-habileo
Valeur: 72.61.98.7
TTL:   300  (5 min pour faciliter les modifs initiales)
```

**⚠️ Pieges rencontres** :

- **Hostinger cree parfois une zone separee** pour le sous-domaine (avec `$ORIGIN api-habileo.couturart.app`). Dans ce cas, c'est le record `@` de cette sous-zone qu'il faut modifier (pas ajouter un `api-habileo` dedans, ca creerait `api-habileo.api-habileo.couturart.app`).
- **Supprimer le record `AAAA`** (IPv6) de la zone du sous-domaine. Il pointait vers l'IPv6 de Hostinger → Let's Encrypt validait en IPv6 et tombait sur Hostinger au lieu du VPS → challenge 404.

### 3.2 Verifier la propagation

```bash
# Depuis plusieurs resolvers
dig @8.8.8.8 A api-habileo.couturart.app +short
dig @1.1.1.1 A api-habileo.couturart.app +short
dig @ns1.dns-parking.com A api-habileo.couturart.app +short

# Tous doivent retourner : 72.61.98.7

# AAAA doit etre vide
dig @8.8.8.8 AAAA api-habileo.couturart.app +short
```

Google 8.8.8.8 peut mettre plus de temps (15-30 min) que Cloudflare. Certbot interroge plusieurs resolvers, donc c'est plutot quand la **majorite** sont a jour qu'il passera.

Si le cache DNS du VPS est en retard :

```bash
sudo resolvectl flush-caches
```

---

## 🔐 Etape 4 — Nginx + HTTPS

### 4.1 Vhost nginx

```bash
sudo nano /etc/nginx/sites-available/api-habileo.couturart.app
```

Contenu initial (HTTP seul, certbot ajoutera le HTTPS) :

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name api-habileo.couturart.app;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        proxy_pass http://127.0.0.1:5100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 180s;
        client_max_body_size 20M;
    }
}
```

Activation :

```bash
sudo ln -s /etc/nginx/sites-available/api-habileo.couturart.app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4.2 Certificat HTTPS via certbot

Une fois le DNS propage (verifier avec `dig`) :

```bash
sudo certbot --nginx -d api-habileo.couturart.app
```

Repondre :

- Email : ton email
- CGU : `A`
- Partager email : `N`
- Rediriger HTTP → HTTPS : `2`

Certbot modifie automatiquement le fichier nginx pour ajouter le bloc HTTPS (port 443) + redirection.

### 4.3 Verifications

```bash
# HTTPS
curl https://api-habileo.couturart.app/api/health
# → {"status":"ok"}

# Redirect HTTP → HTTPS
curl -I http://api-habileo.couturart.app/api/health
# → HTTP/1.1 301 Moved Permanently
#    Location: https://api-habileo.couturart.app/...

# Renouvellement auto
sudo systemctl status certbot.timer
# → active (waiting)

# Test renouvellement (sans vraiment renouveler)
sudo certbot renew --dry-run
# → success
```

Le certificat expire dans **90 jours** et se renouvelle automatiquement ~30 jours avant.

---

## 🔄 Workflow de mise a jour (pour les versions futures)

Pour deployer une nouvelle version (ex: `v1.1.3`) :

### Sur la machine locale

```bash
cd ~/Bureau/Projet-IA/habileo

# 1. Faire tes modifs sur le code
# 2. Tester en local
docker compose up --build

# 3. Si OK, push sur Docker Hub
./deploy.sh v1.1.3
```

### Sur le VPS

```bash
ssh admin@srv1096720
cd ~/projects/habileo

# Mettre a jour le tag dans docker-compose.yml
sed -i 's|:v1.1.2|:v1.1.3|g' docker-compose.yml

# Pull + restart
docker compose pull
docker compose up -d

# Verifier
docker compose ps
curl https://api-habileo.couturart.app/api/health
```

**Downtime** : ~5-10 secondes le temps que l'ancien container s'arrete et le nouveau demarre.

---

## 🧯 Rollback rapide

Si la nouvelle version casse quelque chose :

```bash
ssh admin@srv1096720
cd ~/projects/habileo
sed -i 's|:v1.1.3|:v1.1.2|g' docker-compose.yml
docker compose pull
docker compose up -d
```

C'est pour ca qu'on garde **tous les tags de version** sur Docker Hub (jamais `docker image rm` sur une version stable en prod).

---

## 📊 Monitoring post-deploy

```bash
# Statut
docker compose ps
docker stats --no-stream habileo-backend

# Logs
docker compose logs -f --tail=100

# Logs nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Usage disk/ram
df -h
free -h
```

---

## 🐞 Problemes rencontres & solutions

| Probleme | Cause | Solution |
| --- | --- | --- |
| `Bind for 0.0.0.0:5000 failed` | Port 5000 deja pris par un autre service | Changer le port expose a `5100` dans `docker-compose.yml` + nginx |
| `Invalid response from ... IPv6 ... 404` | Record AAAA de la zone DNS pointe vers Hostinger, Let's Encrypt valide en IPv6 | Supprimer le record AAAA dans la zone du sous-domaine chez Hostinger |
| `dig` retourne encore l'ancienne IP | Cache local ou chez Google DNS | `sudo resolvectl flush-caches`, attendre 15-30 min pour Google |
| `nginx: unexpected end of file, expecting "}"` | Accolade manquante dans le vhost | Re-editer le fichier et verifier que chaque `{` a son `}` |
| Zone DNS avec `$ORIGIN api-habileo.couturart.app` | Hostinger cree une sous-zone separee | Modifier le `@ A` de cette sous-zone (pas ajouter `api-habileo` dedans) |

---

## 🔗 Fichiers de config cles

| Emplacement | Contenu |
| --- | --- |
| `~/projects/habileo/docker-compose.yml` | Orchestration Docker |
| `~/projects/habileo/backend.env` | Secrets (Replicate, Cloudinary) — `chmod 600` |
| `/etc/nginx/sites-available/api-habileo.couturart.app` | Vhost nginx |
| `/etc/nginx/sites-enabled/api-habileo.couturart.app` | Symlink actif |
| `/etc/letsencrypt/live/api-habileo.couturart.app/` | Certificats SSL |

---

## 📚 Docs liees

- [README principal](./README.md) — vue d'ensemble du projet
- [DEPLOY.md](./DEPLOY.md) — pipeline generique de deploiement
- [DOCKER.md](./DOCKER.md) — reference Docker
- [Backend README](./backend/README.md) — API Flask
