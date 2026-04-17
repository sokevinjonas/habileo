# 🧠 Habileo Backend API

Backend Flask pour la plateforme d'essayage virtuel Habileo. Gere l'upload d'images, la validation multi-niveaux et l'orchestration du pipeline IA (Replicate).

---

## 🚀 Fonctionnalites

- Upload d'images vers Cloudinary
- **Validation format** (Pillow) — extension, dimensions, orientation
- **Validation contenu** (moondream2 VLM) — detecte si la photo est bien une personne / un vetement
- **Pipeline try-on en 2 etapes** (remove-bg + IDM-VTON)
- Retry automatique sur rate limits
- Endpoint de healthcheck

---

## 🧱 Stack

- Python 3.11 🐍
- Flask 3 + Flask-CORS ⚡
- Gunicorn (prod) + Docker 🐳
- Pillow (validation images) 🖼️
- Cloudinary SDK ☁️
- Replicate API 🤖

---

## 📁 Structure

```text
backend/
├── app/
│   ├── __init__.py              # Factory Flask + CORS
│   ├── config.py                # Variables d'env
│   ├── routes/
│   │   └── tryon.py             # POST /api/try-on, GET /api/health
│   ├── services/
│   │   ├── replicate_service.py # Pipeline IA (remove-bg + IDM-VTON)
│   │   ├── content_validator.py # Validation VLM via moondream2
│   │   └── storage_service.py   # Upload Cloudinary
│   └── utils/
│       └── helpers.py           # Validation format/taille (Pillow)
├── run.py                       # Entree WSGI
├── requirements.txt
├── Dockerfile                   # Python 3.11-slim + Gunicorn
├── .dockerignore
└── .env.example
```

---

## ⚙️ Configuration

Copier `.env.example` vers `.env` puis renseigner :

| Variable                  | Description                                                 |
| ------------------------- | ----------------------------------------------------------- |
| `REPLICATE_API_TOKEN`     | Token API Replicate                                         |
| `REPLICATE_MODEL_VERSION` | Hash de version d'IDM-VTON (juste le hash, sans `owner/`)   |
| `REPLICATE_POLL_INTERVAL` | Intervalle polling Replicate en secondes (defaut 2)         |
| `REPLICATE_TIMEOUT`       | Timeout total pipeline en secondes (defaut 180)             |
| `CLOUDINARY_URL`          | URL Cloudinary (`cloudinary://key:secret@cloud_name`)       |
| `MAX_UPLOAD_MB`           | Taille max par upload (defaut 10)                           |
| `FLASK_DEBUG`             | `1` en dev, `0` en prod                                     |
| `SECRET_KEY`              | Cle Flask (change-me en prod)                               |
| `PORT`                    | Port d'ecoute (defaut 5000)                                 |

---

## 🧪 Lancement en local (sans Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis editer
python run.py
```

---

## 🐳 Lancement Docker

Depuis la racine du projet :

```bash
docker compose up --build backend
```

Voir [DOCKER.md](../DOCKER.md) pour les details.

---

## 📡 Endpoints

### `GET /api/health`

Healthcheck simple.
```json
{ "status": "ok" }
```

### `POST /api/try-on`

Generation d'un essayage virtuel.

**Body** (multipart/form-data) :

| Champ          | Type   | Requis | Description                              |
| -------------- | ------ | ------ | ---------------------------------------- |
| `user`         | file   | oui    | Photo de la personne (min 300x400, portrait) |
| `cloth`        | file   | oui    | Photo du vetement (min 200x200)          |
| `zone`         | string | oui    | `haut` \| `bas` \| `tout`                |
| `garment_desc` | string | non    | Description texte du vetement            |

**Reponse 200 OK :**
```json
{ "image": "https://replicate.delivery/.../output.jpg" }
```

**Reponse 400 (validation) :**
```json
{
  "error": "La photo doit etre en portrait (verticale).",
  "field": "user"
}
```

**Reponse 502 (erreur pipeline) :**
```json
{ "error": "Essayage virtuel: generation failed" }
```

---

## 🛡️ Validation en cascade

```
Upload
  ↓
[1] Format (Pillow, local, gratuit)
    • Extension (png, jpg, jpeg, webp)
    • Dimensions (user: 300x400 min, cloth: 200x200 min)
    • Orientation portrait pour user
  ↓
[2] Upload Cloudinary
  ↓
[3] Contenu (moondream2, ~$0.001/image, parallele)
    • "Est-ce une personne ?" pour user_photo
    • "Est-ce un vetement ?" pour cloth_photo
  ↓
[4] Pipeline IA (remove-bg + IDM-VTON)
```

Chaque etape renvoie une erreur claire avec le `field` concerne (`user`, `cloth`, `zone`).

---

## 🤖 Pipeline IA

### Etape 1 — Nettoyage du vetement (`lucataco/remove-bg`)

Supprime l'arriere-plan, les mains, le cintre, le mannequin de l'image du vetement. Resilient : si l'etape echoue, le pipeline continue avec l'image originale.

**Cost :** ~$0.01 par image

### Etape 2 — Essayage virtuel (`cuuupid/idm-vton`)

Applique le vetement nettoye sur la photo utilisateur.

**Parametres envoyes :**
- `human_img` : photo utilisateur (URL Cloudinary)
- `garm_img` : vetement nettoye (URL remove-bg output)
- `garment_des` : description texte du vetement
- `category` : `upper_body` / `lower_body` / `dresses`
- `crop: true` — gere les photos qui ne sont pas en ratio 3:4
- `steps: 40` — plus de qualite (defaut 30)
- `seed: 0` — aleatoire

**Cost :** ~$0.03 par generation

---

## 🔁 Retry & resilience

- **429 rate limit :** retry automatique jusqu'a 3 fois avec backoff (5s, 10s, 15s)
- **Step 1 echoue :** pipeline continue avec l'image originale
- **Timeout pipeline :** 180s par defaut (configurable via `REPLICATE_TIMEOUT`)
- **moondream2 indisponible :** validation contenu est skipped, format + pipeline continuent

---

## 💰 Cout estime par generation

| Etape                       | Cout      |
| --------------------------- | --------- |
| Validation user (moondream) | ~$0.001   |
| Validation cloth (moondream)| ~$0.001   |
| Etape 1 — remove-bg         | ~$0.01    |
| Etape 2 — IDM-VTON          | ~$0.03    |
| **Total**                   | **~$0.04** |

---

## 🐞 Depannage

| Probleme                                        | Cause probable                          |
| ----------------------------------------------- | --------------------------------------- |
| `REPLICATE_API_TOKEN manquant`                  | `.env` non rempli                       |
| `402 Payment Required`                          | Credits Replicate epuises               |
| `422 Unprocessable Entity`                      | Mauvais noms de parametres IDM-VTON     |
| `429 Too Many Requests`                         | Rate limit (retry auto, ou attendre)    |
| `La photo doit etre en portrait`                | Photo utilisateur en paysage            |
| `L'image ne semble pas contenir une personne`   | Photo non-humaine detectee par VLM      |
| Upload Cloudinary echoue                        | `CLOUDINARY_URL` mal configure          |
