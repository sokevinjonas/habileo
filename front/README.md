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
- **Galerie personnelle** stockee sur Cloudinary, identifiee par device_id 🖼️
- Gestion des etats offline / vide / erreur avec pull-to-refresh 🔄
- Modal Premium (1 000 FCFA one-time) 💎
- **Monetisation AdMob** (banners + interstitials, skip si premium) 📢
- Messages d'erreur clairs si upload invalide ⚠️

---

## 🧱 Stack technique

- Ionic 8 ⚡
- Angular 20 (standalone components) 🅰️
- Capacitor 8 📱
- TypeScript 5.9 📘
- SCSS + animations CSS 🎨
- nginx en production (reverse proxy + SPA fallback) 🐳

**Plugins Capacitor** :

- `@capacitor/device` — Device ID unique
- `@capacitor-community/admob` — Monetisation (banners + interstitials)

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
│   │   ├── environment.ts          # apiUrl + IDs AdMob de TEST (dev)
│   │   └── environment.prod.ts     # apiUrl relatif + vrais IDs AdMob (prod)
│   └── app/
│       ├── app.component.ts        # Racine + init AdMob
│       ├── app.routes.ts
│       ├── tabs/                   # Bottom tab bar (3 onglets)
│       ├── home/                   # Accueil (+ banner AdMob)
│       ├── try-on/                 # Essayage (+ interstitial apres generation)
│       ├── result/                 # Resultat (+ activation premium)
│       ├── gallery/                # Galerie (+ banner AdMob)
│       ├── components/
│       │   └── loading-overlay/    # Orbe + messages par etapes pipeline
│       └── services/
│           ├── tryon.service.ts    # POST /api/try-on
│           ├── gallery.service.ts  # GET/DELETE /api/gallery
│           ├── device.service.ts   # Device ID (Capacitor ou UUID)
│           ├── premium.service.ts  # Statut premium (localStorage)
│           └── ad.service.ts       # Wrapper AdMob
├── angular.json
├── capacitor.config.ts             # appId + App ID AdMob
├── ionic.config.json
├── package.json
├── Dockerfile                      # Multi-stage : Node build → nginx serve
├── Dockerfile.dev                  # Hot-reload ng serve
├── nginx.conf                      # Proxy /api + SPA fallback
└── .dockerignore
```

---

## 🆔 Device ID (pas de login)

Pour eviter toute friction de sign-up, Habileo identifie chaque utilisateur par un **device_id unique** genere a l'installation.

**Strategie** ([device.service.ts](src/app/services/device.service.ts)) :

1. **Mobile natif** → `Capacitor.Device.getId()` (stable sur iOS/Android)
2. **Web** → UUID genere via `crypto.randomUUID()` et stocke dans `localStorage`
3. Mise en cache en memoire pour eviter de relire le storage a chaque appel

Le device_id est envoye dans chaque requete `/api/try-on` et `/api/gallery`. Cote backend, il sert a isoler les galeries dans Cloudinary (`habileo/users/{device_id}/`).

**Limitation connue :** si l'user reinstalle l'app / change de telephone, il perd sa galerie. Un **code de recuperation** sera ajoute lors du paiement premium pour permettre la restauration.

---

## 🖼️ Galerie

La page [gallery.page.ts](src/app/gallery/gallery.page.ts) gere **5 etats** :

| Etat       | Affichage                                            |
| ---------- | ---------------------------------------------------- |
| `loading`  | Spinner                                              |
| `offline`  | Icone offline + message "Connexion requise"          |
| `error`    | Message d'erreur + bouton Reessayer                  |
| `empty`    | Icone + CTA "Creer un look"                          |
| `ready`    | Grille 2 colonnes des looks                          |

- **Pull-to-refresh** (`ion-refresher`) pour recharger manuellement
- **Refresh automatique** quand on revient sur la page (`ionViewWillEnter`)
- Chaque tuile clique envoie vers `/tabs/result` avec `queryParams: { after: url }` pour reafficher

Les looks sont persistes cote backend dans Cloudinary au format `habileo/users/{device_id}/{id}.jpg`.

---

## 📢 Monetisation AdMob

**Strategie :** freemium avec pubs + premium one-time 1 000 FCFA pour les enlever.

**Placements :**

- **Banner adaptatif** (bas d'ecran) sur Accueil + Galerie
- **Interstitial** 1x max par session, apres une generation try-on reussie

**Architecture** (voir [ADMOB.md](../ADMOB.md) pour les details) :

```text
AppComponent.ngOnInit()
    └ AdService.init()  ← initialise AdMob une fois au demarrage

Home/Gallery pages
    ├ ionViewDidEnter → showBanner()
    └ ionViewWillLeave → hideBanner()

Try-on page
    └ generate() success → showInterstitial() → navigate result

Premium activation (result page modal)
    ├ PremiumService.activate()
    └ AdService.onPremiumActivated() → removeBanner()
```

**Securite :**

- `canRun()` skip automatiquement sur web (AdMob natif uniquement)
- `canRun()` skip si `premium.isPremium` = true
- IDs de **test Google** en dev (`environment.ts`), vrais IDs en prod (`environment.prod.ts`)

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

**IDs AdMob :**

- Dev : IDs de TEST universels Google (no-risk, pubs factices)
- Prod : tes vrais IDs dans `environment.prod.ts`
- App ID AdMob dans [capacitor.config.ts](capacitor.config.ts)

**Tailles limites d'upload** : appliquees cote backend (voir [backend README](../backend/README.md)). Le front ne fait pas de validation stricte — il laisse le backend repondre.

---

## 🧪 Lancement en local (sans Docker)

```bash
cd front
npm install
npx ng serve
```

Ouvre `http://localhost:4200`. L'API doit tourner sur `http://localhost:5000`.

**Note :** sur web, les pubs AdMob ne s'affichent pas (skip auto). Pour les tester il faut builder l'app Android/iOS.

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

Le projet integre Capacitor 8 et les plugins `@capacitor/device` + `@capacitor-community/admob`.

**appId** : `com.habileo.app` (defini dans `capacitor.config.ts`).

### Build Android

```bash
npm run build
npx cap add android
npx cap sync android        # synchronise le web build + plugins
npx cap open android        # ouvre Android Studio
```

### Build iOS (macOS uniquement)

```bash
npx cap add ios
npx cap sync ios
npx cap open ios
```

### Tester AdMob sur emulateur

Lance l'app sur un emulateur Android. Tu verras :

- **Banners** sur Accueil + Galerie (pub test "Test Ad")
- **Interstitial** apres ton 1er try-on (plein ecran, pub factice)

En dev, les **IDs de test Google** sont utilises automatiquement — aucun risque de ban.

---

## 🔄 Integration backend

Deux services HTTP :

### `TryOnService.generate(userFile, clothFile, zone, garmentDesc)`

Envoie un `multipart/form-data` vers `POST /api/try-on`, inclut automatiquement le `device_id` via `DeviceService`.

### `GalleryService.fetchGallery()` / `deleteItem(publicId)`

Appelle `GET /api/gallery?device_id=xxx` et renvoie la liste des looks. Filtre par device_id automatiquement.

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

---

## 📚 Docs liees

- [README principal](../README.md) — vue d'ensemble du projet
- [Backend README](../backend/README.md) — API + pipeline IA
- [DOCKER.md](../DOCKER.md) — infra Docker
- [ADMOB.md](../ADMOB.md) — architecture monetisation
