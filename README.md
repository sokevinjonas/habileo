# 🧠 Habileo — Virtual Try-On Platform

**Habileo** est une plateforme SaaS d'essayage virtuel propulsée par l'IA. Les utilisateurs uploadent une photo d'eux et une image de vêtement, et l'IA génère un rendu réaliste de la tenue portée.

Inspiré des besoins du marché africain (mode wax, boubou, kaba), Habileo permet aux clients de "voir" une tenue sur eux avant commande/confection.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       UTILISATEUR                            │
│            (navigateur / mobile via Capacitor)               │
└──────────────────────────────────────────────────────────────┘
                            │
                    http://localhost:8080
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  FRONTEND (Ionic + Angular 20 + nginx)                       │
│  • UI mobile-first                                           │
│  • Pages: Accueil, Essayer, Resultat, Galerie                │
│  • Proxy /api/* → backend                                    │
└──────────────────────────────────────────────────────────────┘
                            │
                 http://backend:5000 (reseau Docker)
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  BACKEND (Python 3.11 + Flask + Gunicorn)                    │
│  • Validation format (Pillow)                                │
│  • Upload Cloudinary                                         │
│  • Validation contenu (moondream2 VLM)                       │
│  • Pipeline try-on (remove-bg + IDM-VTON)                    │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  SERVICES EXTERNES                                           │
│  • Cloudinary — hebergement images                           │
│  • Replicate — modeles IA (remove-bg, moondream2, IDM-VTON)  │
└──────────────────────────────────────────────────────────────┘
```

---

## 📁 Structure du projet

```
habileo/
├── README.md                 # Ce fichier
├── DOCKER.md                 # Documentation Docker complete
├── docker-compose.yml        # Orchestration prod
├── docker-compose.dev.yml    # Orchestration dev (hot-reload)
├── .gitignore
│
├── backend/                  # API Flask
│   ├── README.md
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example
│   ├── requirements.txt
│   ├── run.py
│   └── app/
│       ├── __init__.py       # Factory Flask
│       ├── config.py         # Variables d'env
│       ├── routes/
│       │   └── tryon.py      # POST /api/try-on, GET /api/health
│       ├── services/
│       │   ├── replicate_service.py    # Pipeline IA (2 etapes)
│       │   ├── content_validator.py    # Validation VLM
│       │   └── storage_service.py      # Upload Cloudinary
│       └── utils/
│           └── helpers.py    # Validation format/taille
│
└── front/                    # App Ionic + Angular
    ├── README.md
    ├── Dockerfile            # Multi-stage build → nginx
    ├── Dockerfile.dev        # Hot-reload ng serve
    ├── nginx.conf            # Reverse proxy /api + SPA fallback
    ├── angular.json
    ├── package.json
    └── src/
        ├── theme/variables.scss      # Palette violet/dore
        ├── global.scss               # Animations, cards, buttons
        ├── environments/
        └── app/
            ├── tabs/                 # Bottom tab bar
            ├── home/                 # Page Accueil
            ├── try-on/               # Page Essayage
            ├── result/               # Page Resultat
            ├── gallery/              # Page Galerie
            ├── components/
            │   └── loading-overlay/
            └── services/
                └── tryon.service.ts
```

---

## 🤖 Pipeline IA (try-on en 2 etapes)

```
Photo vetement (mannequin/cintre/fond complexe)
        ↓
  Etape 1 — lucataco/remove-bg
  Isole le vetement, supprime fond/mannequin
        ↓
  Vetement seul sur fond transparent
        ↓
  Etape 2 — cuuupid/idm-vton
  Applique le vetement sur la photo utilisateur
        ↓
  Resultat final
```

**Validations avant le pipeline :**
1. **Format** (local, Pillow) — extension, dimensions min/max, orientation portrait
2. **Contenu** (moondream2 VLM) — verifie qu'il y a bien une personne et un vetement
3. **Upload** (Cloudinary) — stockage des images

**Cout par generation :** ~$0.04 (rembg $0.01 + idm-vton $0.03 + validation $0.002)
**Temps moyen :** 20-40 secondes

---

## 🚀 Demarrage rapide

### Prerequis

- Docker >= 24 + Docker Compose v2
- Compte [Replicate](https://replicate.com) avec credits
- Compte [Cloudinary](https://cloudinary.com) (gratuit)

### Installation

```bash
# 1. Cloner le repo
git clone https://github.com/sokevinjonas/habileo.git
cd habileo

# 2. Configurer le backend
cp backend/.env.example backend/.env
# Editer backend/.env avec tes vraies cles :
#   - REPLICATE_API_TOKEN
#   - REPLICATE_MODEL_VERSION (IDM-VTON)
#   - CLOUDINARY_URL

# 3. Lancer
docker compose up --build
```

- Backend : <http://localhost:5000/api>
- Frontend : <http://localhost:8080>
- Healthcheck : <http://localhost:5000/api/health>

### Mode developpement (hot-reload)

```bash
docker compose -f docker-compose.dev.yml up --build
```

- Backend : <http://localhost:5000> (reload auto)
- Frontend : <http://localhost:8100> (hot-reload Angular)

---

## 📡 API

### `GET /api/health`

```json
{ "status": "ok" }
```

### `POST /api/try-on`

Multipart form-data :

| Champ          | Type   | Requis | Description                              |
| -------------- | ------ | ------ | ---------------------------------------- |
| `user`         | file   | oui    | Photo de la personne (portrait, min 300x400) |
| `cloth`        | file   | oui    | Photo du vetement (min 200x200)          |
| `zone`         | string | oui    | `haut` / `bas` / `tout`                  |
| `garment_desc` | string | non    | Description du vetement pour guider l'IA |

**Reponse succes :**
```json
{ "image": "https://replicate.delivery/..." }
```

**Reponse erreur :**
```json
{
  "error": "L'image ne semble pas contenir une personne visible...",
  "field": "user"
}
```

**Exemple cURL :**
```bash
curl -X POST http://localhost:5000/api/try-on \
  -F "user=@moi.jpg" \
  -F "cloth=@tshirt.png" \
  -F "zone=haut" \
  -F "garment_desc=chemise col mao grise"
```

---

## 🛠️ Stack technique

**Backend**
- Python 3.11, Flask 3, Gunicorn
- Cloudinary (stockage images)
- Replicate (orchestration IA)
- Pillow (validation format)

**Frontend**
- Ionic 8 + Angular 20 (standalone components)
- Capacitor 8 (prete pour iOS/Android)
- TypeScript 5.9, SCSS
- nginx (production, reverse proxy)

**Infra**
- Docker multi-stage builds
- Docker Compose (prod + dev)
- Docker Hub : `sokevinjonas/habileo-backend` et `sokevinjonas/habileo-frontend`

**Modeles IA (Replicate)**
- `cuuupid/idm-vton` — virtual try-on (1.4M+ runs)
- `lucataco/remove-bg` — suppression arriere-plan (15M+ runs)
- `lucataco/moondream2` — validation contenu VLM (10M+ runs)

---

## 🎯 Fonctionnalites

**Utilisateur**
- Upload photo (camera ou galerie)
- Upload vetement
- Selection zone (haut / bas / tout le corps)
- Description optionnelle du vetement
- Slider avant/apres interactif
- Modal Premium (1 000 FCFA pour debloquer telechargement/partage)
- Galerie des looks sauvegardes

**Technique**
- Validation multi-niveaux (format + IA)
- Pipeline resilient (fallback si remove-bg echoue)
- Retry automatique sur rate limit 429
- Messages d'erreur clairs en francais
- Healthchecks actifs
- Mode dev avec hot-reload

---

## 🐳 Docker

Voir **[DOCKER.md](./DOCKER.md)** pour la documentation complete (Dockerfiles, commandes, depannage).

---

## 📚 Documentation detaillee

- [Backend README](./backend/README.md) — API Flask, pipeline IA, configuration
- [Frontend README](./front/README.md) — Pages, composants, theme
- [Docker guide](./DOCKER.md) — Images, compose, dev vs prod

---

## 📝 Licence

Projet personnel — © 2026 Habileo.

Les modeles IA utilises sont soumis a leurs propres licences :
- IDM-VTON : usage non-commercial uniquement
- moondream2 : Apache 2.0
- remove-bg (BriaAI RMBG) : libre
