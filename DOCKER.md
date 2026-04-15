# 🐳 Docker — Guide Habileo

Ce document explique la configuration Docker du projet, comment elle fonctionne, et comment lancer l'application en **développement** ou en **production**.

---

## 📦 Vue d'ensemble

Le projet contient deux services :

| Service     | Dossier     | Stack                         | Port prod | Port dev |
| ----------- | ----------- | ----------------------------- | --------- | -------- |
| `backend`   | `./backend` | Python 3.11 + Flask + Gunicorn| 5000      | 5000     |
| `frontend`  | `./front`   | Ionic + Angular 20 + nginx    | 8080      | 8100     |

Ils communiquent via un **réseau Docker dédié** `habileo`. Le frontend appelle le backend via `http://backend:5000` à l'intérieur du réseau, ou `http://localhost:5000` depuis l'hôte.

---

## 🗂️ Fichiers Docker

```text
habileo/
├── docker-compose.yml           # orchestration PROD (back + front + network)
├── docker-compose.dev.yml       # orchestration DEV (hot-reload, volumes)
│
├── backend/
│   ├── Dockerfile               # image Python 3.11-slim + Gunicorn
│   ├── .dockerignore            # exclusions build (venv, .env, .git...)
│   └── .env.example             # variables à remplir dans .env
│
└── front/
    ├── Dockerfile               # multi-stage : build Node → serveur nginx
    ├── Dockerfile.dev           # dev : ng serve avec hot-reload
    ├── nginx.conf               # config nginx (SPA fallback, gzip, cache)
    └── .dockerignore
```

---

## 🔧 Backend — `backend/Dockerfile`

Image basée sur `python:3.11-slim`.

**Ce qu'elle fait :**

1. Installe les dépendances système (`build-essential`, `curl` pour le healthcheck).
2. Installe les deps Python depuis `requirements.txt` + `gunicorn`.
3. Copie le code applicatif.
4. Crée un user non-root `appuser` (sécurité).
5. Expose le port **5000**.
6. Lance **Gunicorn** en prod (2 workers, timeout 180s) sur `run:app`.
7. Healthcheck : `GET /api/health` toutes les 30s.

**Pourquoi Gunicorn et pas `flask run` ?**
Flask dev server est monothread et non sécurisé. Gunicorn est un serveur WSGI solide, multi-workers, adapté à la prod.

---

## 🎨 Frontend — `front/Dockerfile` (prod, multi-stage)

**Stage 1 — build :**

- Image `node:20-alpine`
- `npm ci` (install reproductible depuis `package-lock.json`)
- `npm run build -- --configuration=production` → génère `/app/www`

**Stage 2 — runtime :**

- Image `nginx:1.27-alpine`
- Copie de `/app/www` (stage 1) vers `/usr/share/nginx/html`
- Applique `nginx.conf` : SPA fallback, gzip, cache assets long
- Expose le port **80** (mappé sur 8080 via compose)

**Pourquoi multi-stage ?**
L'image finale ne contient **ni Node ni npm ni node_modules** — uniquement les fichiers statiques + nginx. Résultat : image ~40 Mo au lieu de ~1 Go.

### `nginx.conf` — points clés

- **SPA fallback** : toutes les URLs inconnues renvoient `index.html` (nécessaire pour le router Angular).
- **Gzip** activé sur JS/CSS/JSON/SVG.
- **Cache immuable** 1 an sur les assets hashés (JS/CSS/fonts/images).

---

## 🚧 Frontend — `Dockerfile.dev` (développement)

- Image `node:20-alpine`
- Lance `ng serve --host 0.0.0.0 --port 8100`
- Avec le montage de volume `./front:/app` (défini dans `docker-compose.dev.yml`), les modifications locales déclenchent un **hot-reload**.
- Le truc `- /app/node_modules` dans les volumes protège le `node_modules` du conteneur d'être écrasé par celui de l'hôte.

---

## 🎼 `docker-compose.yml` (production)

```yaml
services:
  backend:   # port 5000:5000, env depuis backend/.env
  frontend:  # port 8080:80, depends_on backend
networks:
  habileo:   # réseau interne partagé
```

- `restart: unless-stopped` : relance auto en cas de crash.
- `healthcheck` sur le backend : docker connaît l'état de santé.
- Pas de volume monté : l'image est **immutable** (comportement prod).

## 🧪 `docker-compose.dev.yml` (développement)

Différences avec la prod :

- **Backend** : `FLASK_DEBUG=1`, lance `python run.py` (reload auto), volume `./backend:/app` monté.
- **Frontend** : utilise `Dockerfile.dev`, port `8100`, volume `./front:/app` monté → hot-reload Angular.

---

## 🚀 Comment lancer

### 1. Prérequis

- Docker ≥ 24
- Docker Compose v2 (intégré à Docker Desktop / `docker compose` en ligne de commande)

### 2. Configuration initiale

```bash
cd ~/Bureau/Projet-IA/habileo
cp backend/.env.example backend/.env
# Éditer backend/.env avec tes vraies clés :
#   - REPLICATE_API_TOKEN
#   - REPLICATE_MODEL_VERSION
#   - CLOUDINARY_URL
```

### 3. Lancer en **production**

```bash
docker compose up --build
```

- Backend : <http://localhost:5000/api>
- Frontend : <http://localhost:8080>
- Healthcheck : <http://localhost:5000/api/health>

En arrière-plan :

```bash
docker compose up -d --build
docker compose logs -f           # suivre les logs
docker compose ps                # état des conteneurs
docker compose down              # tout arrêter
```

### 4. Lancer en **développement** (hot-reload)

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

## 🧰 Commandes utiles

| Action                              | Commande                                              |
| ----------------------------------- | ----------------------------------------------------- |
| Rebuild forcé (sans cache)          | `docker compose build --no-cache`                     |
| Logs d'un service                   | `docker compose logs -f backend`                      |
| Shell dans le conteneur backend     | `docker compose exec backend sh`                      |
| Shell dans le conteneur frontend    | `docker compose exec frontend sh`                     |
| Supprimer volumes/networks orphelins| `docker compose down -v --remove-orphans`             |
| Voir les images                     | `docker images \| grep habileo`                       |
| Nettoyage global Docker             | `docker system prune -a`                              |

---

## 🔐 Sécurité & bonnes pratiques appliquées

- ✅ **User non-root** dans le conteneur backend (`appuser`)
- ✅ **Multi-stage build** frontend → image finale minimale, pas d'outils de build embarqués
- ✅ **`.dockerignore`** : `.env`, `.git`, `node_modules`, venv jamais copiés dans l'image
- ✅ **Healthchecks** actifs sur les deux services
- ✅ **Réseau isolé** `habileo` : les conteneurs communiquent entre eux, pas d'exposition inutile
- ✅ **`.env` non commité** (via `.gitignore`) — seul `.env.example` est versionné

---

## 🐞 Dépannage

**`backend/.env` manquant** → `cp backend/.env.example backend/.env` et remplir.

**Port 5000 ou 8080 déjà utilisé** → modifier le mapping dans `docker-compose.yml` (`"5001:5000"`).

**Le frontend ne joint pas le backend** → depuis le navigateur, utiliser `http://localhost:5000`. Depuis le conteneur frontend, utiliser `http://backend:5000`.

**Build frontend OOM / très lent** → augmenter la RAM allouée à Docker Desktop (≥ 4 Go recommandés pour Angular 20).

**Changements non pris en compte** → `docker compose up --build` (force un rebuild des images).

**Cache npm corrompu** → `docker compose build --no-cache frontend`.

---

## 📚 Ressources

- [Docker docs](https://docs.docker.com/)
- [Compose spec](https://docs.docker.com/compose/compose-file/)
- [Gunicorn](https://docs.gunicorn.org/)
- [nginx SPA config](https://router.vuejs.org/guide/essentials/history-mode.html#Example-Server-Configurations)
