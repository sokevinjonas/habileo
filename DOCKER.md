# 🐳 Docker — Guide Habileo

Ce document explique la configuration Docker du projet, comment elle fonctionne, et comment lancer l'application en **developpement** ou en **production**.

---

## 📦 Vue d'ensemble

Le projet contient deux services :

| Service    | Dossier     | Stack                           | Port prod | Port dev |
| ---------- | ----------- | ------------------------------- | --------- | -------- |
| `backend`  | `./backend` | Python 3.11 + Flask + Gunicorn  | 5000      | 5000     |
| `frontend` | `./front`   | Ionic + Angular 20 + nginx      | 8080      | 8100     |

Les deux services communiquent via un **reseau Docker dedie** `habileo`. Le frontend appelle le backend via `http://backend:5000` a l'interieur du reseau.

En production, nginx (dans le conteneur frontend) fait office de **reverse proxy** : il sert les fichiers statiques ET forwarde `/api/*` vers le backend. Du coup, le navigateur ne parle qu'a un seul endpoint (`http://localhost:8080`) et il n'y a pas de probleme CORS.

---

## 🗂️ Fichiers Docker

```text
habileo/
├── docker-compose.yml           # Orchestration PROD (back + front + network)
├── docker-compose.dev.yml       # Orchestration DEV (hot-reload, volumes)
│
├── backend/
│   ├── Dockerfile               # Python 3.11-slim + Gunicorn
│   ├── .dockerignore
│   └── .env.example
│
└── front/
    ├── Dockerfile               # Multi-stage : Node build → nginx
    ├── Dockerfile.dev           # Hot-reload ng serve
    ├── nginx.conf               # Reverse proxy /api + SPA fallback
    └── .dockerignore
```

---

## 🔧 Backend — `backend/Dockerfile`

Image basee sur `python:3.11-slim`.

**Ce qu'elle fait :**

1. Installe les deps systeme (`build-essential`, `curl` pour le healthcheck)
2. Installe les deps Python depuis `requirements.txt` + `gunicorn`
3. Copie le code applicatif
4. Cree un user non-root `appuser` (securite)
5. Expose le port **5000**
6. Lance **Gunicorn** en prod (2 workers, timeout 180s) sur `run:app`
7. Healthcheck sur `GET /api/health` toutes les 30s

**Pourquoi Gunicorn et pas `flask run` ?**
Flask dev server est monothread et non securise. Gunicorn est un serveur WSGI solide, multi-workers, adapte a la prod.

**Dependances Python :**

- Flask 3, flask-cors, requests, python-dotenv
- cloudinary (upload images)
- Pillow (validation dimensions)
- gunicorn (ajoute au build)

---

## 🎨 Frontend — `front/Dockerfile` (prod, multi-stage)

**Stage 1 — build :**

- Image `node:20-alpine`
- `npm ci` (install reproductible depuis `package-lock.json`)
- `npm run build -- --configuration=production` → genere `/app/www`

**Stage 2 — runtime :**

- Image `nginx:1.27-alpine` + `curl` (pour healthcheck)
- Copie de `/app/www` (stage 1) vers `/usr/share/nginx/html`
- Applique `nginx.conf` : proxy `/api/*` vers `http://backend:5000`, SPA fallback, gzip, cache assets
- Expose le port **80** (mappe sur 8080 via compose)

**Pourquoi multi-stage ?**
L'image finale ne contient **ni Node ni npm ni node_modules** — uniquement les fichiers statiques + nginx. Resultat : image ~40 Mo au lieu de ~1 Go.

### `nginx.conf` — points cles

```nginx
location /api/ {
    proxy_pass http://backend:5000/api/;
    proxy_read_timeout 180s;
}

location / {
    try_files $uri $uri/ /index.html;   # SPA fallback
}
```

- **Reverse proxy** : `/api/*` → backend (pas de CORS, meme origine)
- **SPA fallback** : toutes les URLs inconnues renvoient `index.html` (Angular router)
- **Gzip** actif sur JS/CSS/JSON/SVG
- **Cache immuable** 1 an sur les assets hashes

---

## 🚧 Frontend — `Dockerfile.dev` (developpement)

- Image `node:20-alpine`
- Lance `ng serve --host 0.0.0.0 --port 8100 --disable-host-check`
- Avec le montage de volume `./front:/app`, les modifications locales declenchent un **hot-reload**
- Le volume anonyme `- /app/node_modules` empeche le `node_modules` du conteneur d'etre ecrase par celui de l'hote

---

## 🎼 `docker-compose.yml` (production)

```yaml
services:
  backend:
    ports: ["5000:5000"]
    env_file: ./backend/.env
    healthcheck: curl /api/health
  frontend:
    ports: ["8080:80"]
    depends_on: [backend]
networks:
  habileo:
```

- `restart: unless-stopped` : relance auto en cas de crash
- `healthcheck` sur les deux services : Docker connait l'etat de sante
- Pas de volume monte : les images sont **immutables** (comportement prod)
- Reseau `habileo` : les conteneurs se trouvent entre eux via leurs noms (`backend`, `frontend`)

---

## 🧪 `docker-compose.dev.yml` (developpement)

Differences avec la prod :

- **Backend** : `FLASK_DEBUG=1`, lance `python run.py` (reload auto), volume `./backend:/app` monte
- **Frontend** : utilise `Dockerfile.dev`, port **8100**, volume `./front:/app` monte → hot-reload Angular

---

## 🚀 Comment lancer

### 1. Prerequis

- Docker >= 24
- Docker Compose v2 (integre a Docker Desktop / `docker compose` en ligne de commande)

### 2. Configuration initiale

```bash
cd ~/Bureau/Projet-IA/habileo
cp backend/.env.example backend/.env
# Editer backend/.env avec tes vraies cles :
#   - REPLICATE_API_TOKEN
#   - REPLICATE_MODEL_VERSION (hash IDM-VTON)
#   - CLOUDINARY_URL
```

### 3. Lancer en **production**

```bash
docker compose up --build
```

- Backend : <http://localhost:5000/api>
- Frontend : <http://localhost:8080>
- Healthcheck : <http://localhost:5000/api/health>

En arriere-plan :

```bash
docker compose up -d --build
docker compose logs -f           # suivre les logs
docker compose ps                # etat des conteneurs
docker compose down              # tout arreter
```

### 4. Lancer en **developpement** (hot-reload)

```bash
docker compose -f docker-compose.dev.yml up --build
```

- Backend : <http://localhost:5000> (reload auto sur modif Python)
- Frontend : <http://localhost:8100> (hot-reload Angular/Ionic)

### 5. Lancer **un seul service**

```bash
docker compose up backend
docker compose up frontend
```

---

## 🚢 Publier les images sur Docker Hub

Les images sont publiees sous le namespace `sokevinjonas/` :

- `sokevinjonas/habileo-backend:v1.0.1` + `:latest`
- `sokevinjonas/habileo-frontend:v1.0.1` + `:latest`

**Processus de publication :**

```bash
# 1. Build
docker compose build

# 2. Tag + Push (une version + latest)
for svc in backend frontend; do
  docker tag habileo-$svc:latest sokevinjonas/habileo-$svc:v1.0.2
  docker tag habileo-$svc:latest sokevinjonas/habileo-$svc:latest
  docker push sokevinjonas/habileo-$svc:v1.0.2
  docker push sokevinjonas/habileo-$svc:latest
done
```

**Requiert** : `docker login` au prealable.

**Verifier les tags publies :**

```bash
docker images | grep sokevinjonas
```

---

## 🧰 Commandes utiles

| Action                                 | Commande                                              |
| -------------------------------------- | ----------------------------------------------------- |
| Rebuild force (sans cache)             | `docker compose build --no-cache`                     |
| Logs d'un service                      | `docker compose logs -f backend`                      |
| Logs du frontend                       | `docker logs -f habileo-frontend`                     |
| Shell dans le conteneur backend        | `docker compose exec backend sh`                      |
| Shell dans le conteneur frontend       | `docker compose exec frontend sh`                     |
| Supprimer volumes/networks orphelins   | `docker compose down -v --remove-orphans`             |
| Voir les images                        | `docker images \| grep habileo`                       |
| Nettoyage global Docker                | `docker system prune -a`                              |
| Statut des healthchecks                | `docker compose ps`                                   |
| Rebuild un seul service                | `docker compose up --build backend`                   |

---

## 🔁 Cache vs no-cache

| Cas                                       | Commande                           |
| ----------------------------------------- | ---------------------------------- |
| Modif code (`.py`, `.ts`, `.html`)        | `docker compose up --build`        |
| Modif `requirements.txt` / `package.json` | `docker compose up --build`        |
| Bug bizarre, image corrompue              | `docker compose build --no-cache`  |

`--build` utilise le cache des layers inchanges (rapide). `--no-cache` rebuild tout depuis zero (lent, plusieurs minutes).

---

## 🔐 Securite & bonnes pratiques appliquees

- ✅ **User non-root** (`appuser`) dans le conteneur backend
- ✅ **Multi-stage build** frontend → image finale minimale
- ✅ **`.dockerignore`** : `.env`, `.git`, `node_modules`, venv jamais copies dans l'image
- ✅ **Healthchecks** actifs sur les deux services
- ✅ **Reseau isole** `habileo` : communication via noms de service
- ✅ **Reverse proxy nginx** : pas de CORS, pas d'URL prod en dur dans le code
- ✅ **`.env` non commite** (via `.gitignore`) — seul `.env.example` est versionne
- ✅ **Retry sur rate limits** Replicate (429) dans le backend

---

## 🐞 Depannage

**`backend/.env` manquant** → `cp backend/.env.example backend/.env` et remplir.

**Port 5000 ou 8080 deja utilise** → modifier le mapping dans `docker-compose.yml` (`"5001:5000"`).

**Frontend unhealthy** → verifier `docker logs habileo-frontend`. Le healthcheck utilise `curl` (installe dans l'image).

**Le frontend ne joint pas le backend** :

- Depuis le navigateur : utiliser `http://localhost:8080/api/...` (nginx proxy)
- Depuis un conteneur : utiliser `http://backend:5000/api/...`

**Build frontend OOM / tres lent** → augmenter la RAM allouee a Docker (>= 4 Go recommandes pour Angular 20).

**Changements non pris en compte** → `docker compose up --build` (force un rebuild des images).

**Cache npm corrompu** → `docker compose build --no-cache frontend`.

**Image pousse meme apres modif** → verifie avec `docker images` que le digest a change. Si non, la modif n'est pas dans l'image → rebuild.

---

## 📚 Ressources

- [Docker docs](https://docs.docker.com/)
- [Compose spec](https://docs.docker.com/compose/compose-file/)
- [Gunicorn](https://docs.gunicorn.org/)
- [nginx reverse proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Habileo backend README](./backend/README.md)
- [Habileo frontend README](./front/README.md)
