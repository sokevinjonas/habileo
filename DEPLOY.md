# 🚀 Deploiement en production — Habileo

Ce guide explique comment deployer Habileo sur un VPS en utilisant les images Docker Hub.

---

## 🏛️ Architecture de deploiement

```text
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│  Machine locale   │       │    Docker Hub     │       │       VPS         │
│  (dev)            │       │                   │       │   (production)    │
│                   │       │                   │       │                   │
│ docker build  ───────────▶│ sokevinjonas/     │──────▶│ docker compose    │
│ docker push               │ habileo-backend   │       │   pull            │
│                           │ habileo-frontend  │       │ docker compose    │
│                           │   :v1.0.x         │       │   up -d           │
│                           │   :latest         │       │                   │
└───────────────────┘       └───────────────────┘       └─────────┬─────────┘
                                                                  │
                                                                  ▼
                                                        User → https://habileo.com
```

**Pourquoi cette architecture ?**

- **Rapide** : le VPS ne build rien, il pull juste des images pre-construites (~30s vs 5-10min)
- **Economique** : ton VPS peut etre un petit gabarit (1-2 GB RAM)
- **Reproductible** : l'image exacte testee en dev est deployee en prod
- **Rollback facile** : retour a une ancienne version = changer un tag

---

## 📦 Versioning des images

| Tag             | Usage                                               |
| --------------- | --------------------------------------------------- |
| `v1.0.0`        | Version stable majeure                              |
| `v1.0.1`        | Patch / hotfix                                      |
| `v1.1.0`        | Nouvelle fonctionnalite                             |
| `latest`        | Pointe toujours vers la derniere version publiee    |

**Regle :** en prod, **toujours tagger une version specifique** (ex: `v1.0.2`). Ne pas se reposer sur `latest` en prod — si tu push une v1.0.3 qui casse quelque chose, ton VPS bascule automatiquement au prochain `pull` et tu n'as pas le temps de tester.

---

## 🛠️ Etape 1 — Preparer le VPS (une seule fois)

### 1.1 Prerequis sur le VPS

- Docker >= 24
- Docker Compose v2 (integre a Docker CE moderne)
- Un domaine/sous-domaine pointe vers l'IP du VPS (ex: `habileo.com` + `api.habileo.com`)
- Ports **80** et **443** ouverts (pas 5000 ou 8080 en prod — tout passe par HTTPS sur 443)

Si Docker n'est pas installe :

```bash
ssh user@vps
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# se deconnecter/reconnecter pour prendre en compte le groupe
```

### 1.2 Creer l'arborescence sur le VPS

```bash
ssh user@vps
mkdir -p /opt/habileo
cd /opt/habileo
```

### 1.3 Fichier `.env` production sur le VPS

```bash
nano /opt/habileo/backend.env
```

Contenu (adapte tes cles) :

```env
# Flask
FLASK_DEBUG=0
SECRET_KEY=<genere-une-cle-aleatoire-longue>
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

**Important :** `chmod 600 backend.env` pour que seul toi puisse le lire.

### 1.4 docker-compose.prod.yml sur le VPS

Voir la section dediee plus bas — cree le fichier `/opt/habileo/docker-compose.yml`.

### 1.5 Reverse proxy + HTTPS

Ton VPS heberge surement d'autres apps (tu as deja un `laravel-db` MySQL). Un reverse proxy est indispensable.

Je recommande **Caddy** — le plus simple (SSL Let's Encrypt automatique, 0 config crypto) :

```bash
mkdir -p /opt/caddy
nano /opt/caddy/Caddyfile
```

Contenu du `Caddyfile` (adapte le domaine) :

```caddy
habileo.com {
    reverse_proxy localhost:8080
}

api.habileo.com {
    reverse_proxy localhost:5000
}
```

Docker Compose pour Caddy :

```yaml
# /opt/caddy/docker-compose.yml
services:
  caddy:
    image: caddy:2-alpine
    container_name: caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    network_mode: host  # pour atteindre localhost:5000 / 8080

volumes:
  caddy_data:
  caddy_config:
```

```bash
cd /opt/caddy && docker compose up -d
```

**C'est tout.** Caddy obtient automatiquement les certificats Let's Encrypt et redirige le trafic vers tes conteneurs Habileo.

---

## 🔧 Etape 2 — docker-compose.prod.yml

A placer dans `/opt/habileo/docker-compose.yml` sur le VPS :

```yaml
services:
  backend:
    image: sokevinjonas/habileo-backend:v1.0.2
    container_name: habileo-backend
    restart: unless-stopped
    ports:
      - "127.0.0.1:5000:5000"   # expose localement uniquement, Caddy proxy devant
    env_file:
      - ./backend.env
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    networks:
      - habileo

  frontend:
    image: sokevinjonas/habileo-frontend:v1.0.2
    container_name: habileo-frontend
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:80"     # expose localement uniquement
    depends_on:
      - backend
    networks:
      - habileo

networks:
  habileo:
    driver: bridge
```

**Differences importantes avec le docker-compose.yml de dev :**

- ❌ Plus de `build:` — on utilise directement `image:` depuis Docker Hub
- ✅ Ports bindes sur `127.0.0.1` uniquement (pas d'exposition publique directe)
- ✅ Tag de version explicite (`v1.0.2`, pas `latest`)

---

## 🚢 Etape 3 — Pipeline de deploiement

### 3.1 Depuis ta machine locale

```bash
# 1. Build les images en mode production
cd ~/Bureau/Projet-IA/habileo
docker compose build

# 2. Tag + push vers Docker Hub
VERSION=v1.0.2

docker tag habileo-backend:latest sokevinjonas/habileo-backend:$VERSION
docker tag habileo-backend:latest sokevinjonas/habileo-backend:latest
docker tag habileo-frontend:latest sokevinjonas/habileo-frontend:$VERSION
docker tag habileo-frontend:latest sokevinjonas/habileo-frontend:latest

docker push sokevinjonas/habileo-backend:$VERSION
docker push sokevinjonas/habileo-backend:latest
docker push sokevinjonas/habileo-frontend:$VERSION
docker push sokevinjonas/habileo-frontend:latest
```

### 3.2 Sur le VPS

```bash
ssh user@vps
cd /opt/habileo

# Mettre a jour la version dans docker-compose.yml
sed -i 's/:v1.0.1/:v1.0.2/g' docker-compose.yml

# Pull + restart
docker compose pull
docker compose up -d

# Verifier
docker compose ps
docker compose logs -f --tail=50
```

---

## 🤖 Automatisation — scripts prets a l'emploi

### `deploy.sh` (sur ta machine locale)

A placer a la racine du projet.

```bash
#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "Usage: ./deploy.sh <version>  (ex: v1.0.2)"
  exit 1
fi

echo "🔨 Build des images..."
docker compose build

echo "🏷️  Tag $VERSION + latest..."
for svc in backend frontend; do
  docker tag habileo-$svc:latest sokevinjonas/habileo-$svc:$VERSION
  docker tag habileo-$svc:latest sokevinjonas/habileo-$svc:latest
done

echo "📤 Push vers Docker Hub..."
for svc in backend frontend; do
  docker push sokevinjonas/habileo-$svc:$VERSION
  docker push sokevinjonas/habileo-$svc:latest
done

echo "✅ Images publiees : sokevinjonas/habileo-{backend,frontend}:$VERSION"
echo ""
echo "👉 Sur le VPS :"
echo "   ssh user@vps 'cd /opt/habileo && sed -i \"s/:v[0-9.]*\\\"$/:$VERSION\\\"/g\" docker-compose.yml && docker compose pull && docker compose up -d'"
```

Rendre executable :

```bash
chmod +x deploy.sh
./deploy.sh v1.0.2
```

### `remote-deploy.sh` (optionnel, pour tout faire en une commande)

```bash
#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"
VPS="user@vps.example.com"
VPS_PATH="/opt/habileo"

if [[ -z "$VERSION" ]]; then
  echo "Usage: ./remote-deploy.sh <version>"
  exit 1
fi

# 1. Push vers Docker Hub (reutilise deploy.sh)
./deploy.sh "$VERSION"

# 2. Mettre a jour la version sur le VPS
echo "🚀 Deploiement sur $VPS..."
ssh "$VPS" <<EOF
  set -e
  cd $VPS_PATH
  sed -i 's|:v[0-9.]*$|:$VERSION|g' docker-compose.yml
  docker compose pull
  docker compose up -d
  docker compose ps
EOF

echo "✅ Deploiement termine — $VERSION est en prod"
```

Utilisation :

```bash
./remote-deploy.sh v1.0.2
# → build + push + deploy d'un coup
```

---

## 🔁 Rollback

Si une version casse la prod, retour a la precedente :

```bash
ssh user@vps
cd /opt/habileo
sed -i 's/:v1.0.2/:v1.0.1/g' docker-compose.yml
docker compose pull
docker compose up -d
```

C'est pour ca qu'on **tagge toutes les versions** — chaque version deployee est restaurable en 30 secondes.

---

## 📊 Monitoring post-deploy

```bash
# Statut des conteneurs
docker compose ps

# Logs en direct
docker compose logs -f

# Usage ressources
docker stats

# Healthcheck
curl https://api.habileo.com/api/health
# → {"status": "ok"}

# Tester une endpoint
curl -s https://api.habileo.com/api/gallery?device_id=test | head
```

---

## 🔐 Securite production

**Obligatoire :**

- ✅ Ports non exposes publiquement (`127.0.0.1:5000` → Caddy proxy devant)
- ✅ HTTPS partout (Caddy auto-SSL)
- ✅ `backend.env` en mode `chmod 600`
- ✅ `SECRET_KEY` Flask aleatoire et long
- ✅ Firewall (`ufw`) bloque tout sauf 22, 80, 443

**Recommande :**

- 🔒 Changer le port SSH de 22 vers 2222 (reduit spam)
- 🔒 Authentification SSH par cle uniquement (`PasswordAuthentication no`)
- 🔒 Fail2ban pour bloquer les brute-force SSH
- 🔒 Rotation des tokens Replicate tous les 6 mois
- 🔒 Backups automatiques (Cloudinary se sauvegarde tout seul, mais backup la VM aussi)

---

## 💾 Sauvegardes

**Cote Cloudinary :** tes images sont deja dans le cloud, Cloudinary les protege (redondance multi-DC). Pas besoin de backup de ton cote.

**Cote VPS :** sauvegarde ces fichiers periodiquement :

- `/opt/habileo/backend.env`
- `/opt/habileo/docker-compose.yml`
- `/opt/caddy/Caddyfile`

Un simple rsync ou scp vers ta machine locale :

```bash
rsync -avz user@vps:/opt/habileo/ ~/backups/habileo/
rsync -avz user@vps:/opt/caddy/Caddyfile ~/backups/habileo/caddy/
```

---

## 🚧 Passage en prod — checklist

Avant de pointer `habileo.com` vers le VPS, verifie :

- [ ] Images buildees et pushees sur Docker Hub avec un tag (pas juste `latest`)
- [ ] `/opt/habileo/backend.env` rempli avec les **vraies** cles prod (pas les `xxxx`)
- [ ] `REPLICATE_API_TOKEN` avec des credits rechargees
- [ ] `CLOUDINARY_URL` valide
- [ ] `environment.prod.ts` du frontend utilise les vrais IDs AdMob (pas les IDs de test)
- [ ] `capacitor.config.ts` a le bon `appId` (`com.habileo.app`)
- [ ] Certificats SSL OK (Caddy doit avoir obtenu Let's Encrypt au premier demarrage)
- [ ] DNS : `habileo.com` et `api.habileo.com` pointent vers l'IP du VPS
- [ ] Test manuel : `curl https://api.habileo.com/api/health` retourne `{"status":"ok"}`
- [ ] Test manuel : `https://habileo.com` charge la page d'accueil
- [ ] Test end-to-end : upload 2 images → try-on → resultat → galerie affiche le look

---

## ⏭️ Evolution future — CI/CD avec GitHub Actions

Quand le projet grandit, on automatise avec GitHub Actions :

```yaml
# .github/workflows/deploy.yml
on:
  push:
    tags: ['v*']

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - run: docker compose build
      - run: |
          docker tag habileo-backend:latest sokevinjonas/habileo-backend:${{ github.ref_name }}
          docker tag habileo-frontend:latest sokevinjonas/habileo-frontend:${{ github.ref_name }}
          docker push sokevinjonas/habileo-backend:${{ github.ref_name }}
          docker push sokevinjonas/habileo-frontend:${{ github.ref_name }}
      - name: Deploy on VPS
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/habileo
            sed -i 's|:v[0-9.]*|:${{ github.ref_name }}|g' docker-compose.yml
            docker compose pull && docker compose up -d
```

Workflow : `git tag v1.0.3 && git push --tags` → auto build + push + deploy sur le VPS. Mais c'est pour plus tard — pour l'instant, les scripts manuels suffisent.

---

## 📚 Ressources

- [Caddy — reverse proxy simple](https://caddyserver.com/docs/)
- [Docker compose file reference](https://docs.docker.com/compose/compose-file/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Habileo README principal](./README.md)
- [DOCKER.md](./DOCKER.md) — images locales + dev
