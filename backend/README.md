# 🧠 Habileo Backend API

Habileo est une plateforme de *virtual try-on* propulsée par l'IA : l'utilisateur envoie une photo de lui et une photo de vêtement, et l'API retourne un rendu réaliste de la tenue portée.

Backend écrit en **Flask**, avec **Replicate** pour l'inférence IA et **Cloudinary** pour l'hébergement des images.

---

## 🚀 Fonctionnalités

- Upload d'une photo utilisateur 👤
- Upload d'un vêtement 👕
- Génération IA du try-on virtuel 🤖
- Stockage d'images sur Cloudinary ☁️
- API REST prête pour mobile (Ionic / Angular)

---

## 🧱 Stack

- Python 3.11 🐍
- Flask + Flask-CORS ⚡
- Replicate API 🤖
- Cloudinary ☁️
- python-dotenv 🔐
- Gunicorn (prod) + Docker 🐳

---

## 📁 Structure

```text
backend/
├── app/
│   ├── __init__.py          # factory Flask
│   ├── config.py            # variables d'env centralisées
│   ├── routes/
│   │   └── tryon.py         # POST /api/try-on, GET /api/health
│   ├── services/
│   │   ├── replicate_service.py   # appel + polling Replicate
│   │   └── storage_service.py     # upload Cloudinary
│   └── utils/
│       └── helpers.py       # validation images
├── run.py                   # entrée WSGI
├── requirements.txt
├── Dockerfile
├── .dockerignore
└── .env.example
```

---

## ⚙️ Configuration

Copier `.env.example` vers `.env` puis renseigner :

| Variable                  | Description                                       |
| ------------------------- | ------------------------------------------------- |
| `REPLICATE_API_TOKEN`     | Token API Replicate                               |
| `REPLICATE_MODEL_VERSION` | ID de version du modèle try-on                    |
| `CLOUDINARY_URL`          | URL Cloudinary (`cloudinary://key:secret@cloud`)  |
| `MAX_UPLOAD_MB`           | Taille max upload (défaut 10)                     |
| `FLASK_DEBUG`             | `1` en dev, `0` en prod                           |

---

## 🧪 Lancer en local (sans Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis éditer
python run.py
```

L'API écoute sur `http://localhost:5000`.

---

## 🐳 Lancer avec Docker

À la racine du projet :

```bash
cp backend/.env.example backend/.env   # puis éditer
docker compose up --build
```

- API : `http://localhost:5000/api`
- Healthcheck : `GET /api/health`

---

## 📡 Endpoints

### `GET /api/health`

Retourne `{"status": "ok"}`.

### `POST /api/try-on`

Multipart form-data :

| Champ   | Type | Description           |
| ------- | ---- | --------------------- |
| `user`  | file | Photo de la personne  |
| `cloth` | file | Photo du vêtement     |

Réponse :

```json
{ "image": "https://replicate.delivery/..." }
```

ou en cas d'erreur :

```json
{ "error": "..." }
```

Exemple :

```bash
curl -X POST http://localhost:5000/api/try-on \
  -F "user=@moi.jpg" \
  -F "cloth=@tshirt.png"
```
