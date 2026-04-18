# 🧠 Habileo Backend API

Backend Flask pour la plateforme d'essayage virtuel Habileo. Gere l'upload d'images, la validation multi-niveaux et l'orchestration du pipeline IA (Replicate).

---

## 🚀 Fonctionnalites

- Upload d'images vers Cloudinary
- **Validation format** (Pillow) — extension, dimensions, orientation
- **Validation contenu** (moondream2 VLM) — detecte si la photo est bien une personne / un vetement
- **Pipeline try-on en 2 etapes** (remove-bg + IDM-VTON)
- **Galerie par device_id** — sauvegarde des resultats dans Cloudinary, isolation par utilisateur
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
│   │   ├── tryon.py             # POST /api/try-on, GET /api/health
│   │   └── gallery.py           # GET /api/gallery, DELETE /api/gallery/<id>
│   ├── services/
│   │   ├── replicate_service.py # Pipeline IA (remove-bg + IDM-VTON)
│   │   ├── content_validator.py # Validation VLM via moondream2
│   │   └── storage_service.py   # Upload + galerie Cloudinary
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

| Champ          | Type   | Requis | Description                                           |
| -------------- | ------ | ------ | ----------------------------------------------------- |
| `user`         | file   | oui    | Photo de la personne (min 300x400, portrait)          |
| `cloth`        | file   | oui    | Photo du vetement (min 200x200)                       |
| `zone`         | string | oui    | `haut` \| `bas` \| `tout`                             |
| `garment_desc` | string | non    | Description texte du vetement                         |
| `device_id`    | string | non    | ID unique de l'appareil → sauvegarde dans la galerie  |

Si `device_id` est fourni, le resultat final est re-uploade dans `habileo/users/{device_id}/` (Cloudinary) et la reponse contient aussi `id` (public_id Cloudinary) pour suppression future.

**Reponse 200 OK :**

```json
{
  "image": "https://res.cloudinary.com/.../habileo/users/abc-123/xyz123.jpg",
  "id": "habileo/users/abc-123/xyz123"
}
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

### `GET /api/gallery?device_id=xxx`

Liste les looks sauvegardes pour un device_id.

**Parametres query** :

| Parametre   | Requis | Description               |
| ----------- | ------ | ------------------------- |
| `device_id` | oui    | ID unique de l'appareil   |

**Reponse 200 OK :**

```json
{
  "items": [
    {
      "id": "habileo/users/abc-123/xyz123",
      "url": "https://res.cloudinary.com/.../xyz123.jpg",
      "date": "2026-04-18T14:32:00Z",
      "label": "chemise col mao grise"
    }
  ],
  "count": 1
}
```

**Reponse 400 :** `{"error": "device_id requis"}`

### `DELETE /api/gallery/<public_id>?device_id=xxx`

Supprime un look de la galerie. Le `public_id` doit appartenir au `device_id` fourni (securite cote backend).

**Reponse 200 OK :** `{"ok": true}`

**Reponse 404 :** `{"error": "Image introuvable ou accès refusé"}`

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
- **Sauvegarde galerie echoue :** try-on renvoie quand meme l'URL Replicate (pas de blocage)

---

## 🖼️ Galerie (stockage par device_id)

### Organisation Cloudinary

```text
Cloudinary/
└── habileo/
    ├── temp/                          # uploads temporaires (user + cloth)
    └── users/
        ├── {device_id_A}/
        │   ├── xyz123.jpg             # resultat d'un try-on
        │   └── abc456.jpg
        └── {device_id_B}/
            └── ...
```

### Securite

- Le `device_id` est **sanitize** avant usage (`[^a-zA-Z0-9_-]` strippe, max 64 chars)
- `delete_gallery_item` verifie que le `public_id` commence par `habileo/users/{device_id}/` avant de supprimer (pas de cross-user)
- Endpoint `GET /api/gallery` **exige** un `device_id` non vide

### Listing

`cloudinary.api.resources(type='upload', prefix='habileo/users/{device_id}/')` — max 50 resultats, tries par date decroissante.

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
| Galerie vide malgre plusieurs try-on            | `device_id` non envoye par le frontend  |
| `device_id requis`                              | Parametre manquant sur `/api/gallery`   |

---

## 📚 Docs liees

- [README principal](../README.md) — vue d'ensemble du projet
- [Frontend README](../front/README.md) — app Ionic + Angular
- [DOCKER.md](../DOCKER.md) — infra Docker
- [ADMOB.md](../ADMOB.md) — architecture monetisation
