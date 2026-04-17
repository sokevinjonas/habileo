# 📱 Habileo Frontend

Application mobile-first d'essayage virtuel propulsee par l'IA, construite avec **Ionic 8 + Angular 20** (standalone components) et **Capacitor 8** (prete pour iOS/Android).

---

## 🚀 Fonctionnalites

- Upload photo utilisateur (camera ou galerie) 👤
- Upload image vetement 👕
- Selection de la zone (haut / bas / tout le corps) 🎯
- Description optionnelle du vetement pour guider l'IA 📝
- Loading overlay avec etapes du pipeline en temps reel ⏳
- Slider avant/apres interactif 🎞️
- Modal Premium (1 000 FCFA) 💎
- Galerie des looks sauvegardes 🖼️
- Messages d'erreur clairs si upload invalide ⚠️

---

## 🧱 Stack technique

- Ionic 8 ⚡
- Angular 20 (standalone components) 🅰️
- Capacitor 8 (iOS/Android) 📱
- TypeScript 5.9 📘
- SCSS + animations CSS 🎨
- nginx en production (reverse proxy + SPA fallback) 🐳

---

## 📁 Structure

```text
front/
├── src/
│   ├── index.html
│   ├── main.ts
│   ├── global.scss                 # Animations, cards, buttons globaux
│   ├── theme/
│   │   └── variables.scss          # Palette violet/dore Habileo
│   ├── environments/
│   │   ├── environment.ts          # apiUrl local
│   │   └── environment.prod.ts     # apiUrl prod (relatif, via nginx proxy)
│   └── app/
│       ├── app.component.ts        # Racine IonApp
│       ├── app.routes.ts
│       ├── tabs/                   # Bottom tab bar
│       │   ├── tabs.page.ts
│       │   ├── tabs.page.html      # 3 onglets (Accueil, Essayer, Galerie)
│       │   └── tabs.routes.ts
│       ├── home/                   # Page Accueil
│       │   ├── home.page.ts
│       │   ├── home.page.html      # Hero + steps + carousel transformations
│       │   └── home.page.scss
│       ├── try-on/                 # Page Essayage
│       │   ├── try-on.page.ts
│       │   ├── try-on.page.html    # 2 uploads + select zone + description
│       │   └── try-on.page.scss
│       ├── result/                 # Page Resultat
│       │   ├── result.page.ts
│       │   ├── result.page.html    # Slider avant/apres + actions + modal premium
│       │   └── result.page.scss
│       ├── gallery/                # Page Galerie
│       │   ├── gallery.page.ts
│       │   ├── gallery.page.html   # Grille 2 colonnes
│       │   └── gallery.page.scss
│       ├── components/
│       │   └── loading-overlay/    # Orbe lumineux + progression pipeline
│       └── services/
│           └── tryon.service.ts    # Appel POST /api/try-on
├── angular.json
├── capacitor.config.ts
├── ionic.config.json
├── package.json
├── Dockerfile                      # Multi-stage : Node build → nginx serve
├── Dockerfile.dev                  # Hot-reload ng serve
├── nginx.conf                      # Proxy /api + SPA fallback
└── .dockerignore
```

---

## 🎨 Design

**Palette :**

| Role       | Couleur   | Usage                                    |
| ---------- | --------- | ---------------------------------------- |
| Primary    | `#4b0082` | Violet profond — actions principales     |
| Accent     | `#c8a03e` | Dore — CTA "Generer", elements premium   |
| Background | `#faf9f7` | Off-white                                |
| Card       | `#ffffff` | Fond des cartes                          |
| Muted      | `#7a6e9a` | Texte secondaire                         |
| Danger     | `#d93025` | Messages d'erreur                        |

**Animations disponibles (global.scss) :**

- `animate-fade-up` — fade + translate Y
- `animate-fade-in` — fade simple
- `animate-scale-in` — scale + fade
- `animate-pulse-glow` — pulsation (loading orb)
- `animate-float` — flottement (loading orb)
- `animate-scan` — ligne de scan qui glisse

**Classes utilitaires :**

- `.card-elevated` — carte blanche avec shadow
- `.card-upload` — carte d'upload en tirets
- `.btn-cta` — bouton CTA dore
- `.btn-primary-gradient` — bouton violet a gradient
- `.gradient-hero` — fond du hero section
- `.scrollbar-hide` — masque la scrollbar

---

## 🗺️ Routes

| Route              | Page           | Description                              |
| ------------------ | -------------- | ---------------------------------------- |
| `/`                | redirect       | vers `/tabs/home`                        |
| `/tabs/home`       | HomePage       | Accueil : hero + steps + transformations |
| `/tabs/try-on`     | TryOnPage      | Upload + zone + generation               |
| `/tabs/result`     | ResultPage     | Slider avant/apres + actions + premium   |
| `/tabs/gallery`    | GalleryPage    | Grille des looks sauvegardes             |

---

## ⚙️ Configuration

**URL de l'API :**

- Dev local : `environment.ts` → `apiUrl: 'http://localhost:5000'`
- Production : `environment.prod.ts` → `apiUrl: ''` (relatif, passe par nginx `/api`)

**Tailles limites d'upload** : appliquees cote backend (voir [backend README](../backend/README.md)). Le front ne fait pas de validation stricte — il laisse le backend repondre.

---

## 🧪 Lancement en local (sans Docker)

```bash
cd front
npm install
npx ng serve
```

Ouvre `http://localhost:4200`. L'API doit tourner sur `http://localhost:5000`.

---

## 🐳 Lancement Docker

Depuis la racine du projet :

```bash
docker compose up --build frontend
```

Accessible sur `http://localhost:8080`. Le build en prod utilise un `Dockerfile` multi-stage : Node 20 pour builder, puis nginx 1.27 pour servir les fichiers statiques (image finale ~40 Mo).

**Mode dev (hot-reload) :**

```bash
docker compose -f ../docker-compose.dev.yml up --build frontend
```

Accessible sur `http://localhost:8100` avec hot-reload Angular.

Voir [DOCKER.md](../DOCKER.md) pour les details.

---

## 📱 Mobile (Capacitor)

Le projet integre Capacitor 8. Pour build les apps natives :

```bash
# Android
npx ng build --configuration=production
npx cap add android
npx cap sync android
npx cap open android

# iOS (macOS uniquement)
npx cap add ios
npx cap sync ios
npx cap open ios
```

**appId** : `io.ionic.starter` (a changer dans `capacitor.config.ts` avant publication).

---

## 🔄 Integration backend

Le service [`TryOnService`](src/app/services/tryon.service.ts) gere l'appel :

```typescript
generate(userFile, clothFile, zone, garmentDesc): Promise<TryOnResult>
```

Envoie un `multipart/form-data` vers `POST /api/try-on`.

**Gestion des erreurs** (voir [try-on.page.ts](src/app/try-on/try-on.page.ts)) :

- Affichage d'une alert Ionic avec le message
- Affichage inline (rouge) sous le champ concerne via `errorField`
- Le message s'efface automatiquement lors d'un nouveau upload

---

## 🎯 Scripts NPM

| Commande              | Action                                 |
| --------------------- | -------------------------------------- |
| `npm start`           | Lance `ng serve` (dev)                 |
| `npm run build`       | Build production                       |
| `npm run watch`       | Build dev en mode watch                |
| `npm test`            | Lance les tests Karma                  |
| `npm run lint`        | ESLint + Angular lint                  |
