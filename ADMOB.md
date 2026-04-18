# 📢 Integration AdMob — Habileo

Ce document explique l'architecture de la monetisation par publicites dans Habileo : fonctionnement, placement, logique d'affichage, et gestion du premium.

---

## 🎯 Strategie economique

**Modele retenu :** Freemium avec pubs + **premium one-time 1 000 FCFA**

| | Gratuit | Premium (1 000 FCFA) |
| --- | --- | --- |
| Generations try-on | Illimitees | Illimitees |
| Galerie | Acces | Acces |
| Banners en bas | Oui | Non |
| Interstitial apres generation | Oui | Non |
| Telechargement HD | Non | Oui |
| Partage social | Non | Oui |
| Sauvegarde galerie | Non | Oui |

Le paiement est **one-time** (pas d'abonnement) — adapte au marche africain ou les paiements recurrents (Mobile Money) sont culturellement peu adoptes.

---

## 🏛️ Architecture

```text
┌────────────────────────────────────────────────────────────┐
│  AppComponent (au demarrage)                               │
│    └ AdService.init()                                      │
│        ├ AdMob.initialize()                                │
│        └ GDPR consent form (auto sur iOS/EU)               │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│  PremiumService  (source de verite du statut premium)      │
│    • isPremium: boolean                                    │
│    • activate() / deactivate()                             │
│    • Persiste dans localStorage                            │
│    • Expose premium$ (Observable) pour reagir en temps reel│
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│  AdService  (wrapper au-dessus de @capacitor-community)    │
│    • showBanner() / hideBanner() / removeBanner()          │
│    • showInterstitial()  (1x max par session)              │
│    • canRun()  → skip sur web + skip si premium            │
│    • onPremiumActivated() → removeBanner()                 │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│  @capacitor-community/admob  (SDK natif iOS/Android)       │
└────────────────────────────────────────────────────────────┘
```

---

## 📍 Placements des annonces

### Banner adaptatif — bas d'ecran

| Page          | Banner ? | Raison                                                |
| ------------- | -------- | ----------------------------------------------------- |
| **Accueil**   | ✅       | Contenu passif, utilisateur scrolle                   |
| **Galerie**   | ✅       | Contenu passif, liste de looks                        |
| **Try-on**    | ❌       | Moment critique UX (upload, attente validation)       |
| **Resultat**  | ❌       | Moment "wow", on laisse la place au look              |

**Taille** : `ADAPTIVE_BANNER` — la taille s'adapte a l'ecran (Google recommande).
**Position** : `BOTTOM_CENTER` avec `margin: 56` pour passer au-dessus de la tab bar Ionic.

### Interstitial — entre 2 ecrans

Declenche **dans `try-on.page.ts` > `generate()`** apres que l'API a renvoye le resultat, **juste avant** la navigation vers la page resultat :

```typescript
if (result.image) {
  await this.ads.showInterstitial();  // pub plein ecran
  this.router.navigate(['/tabs/result'], { queryParams: {...} });
}
```

**Pourquoi a ce moment ?**

- L'utilisateur vient d'attendre 30-40s pour sa generation, il est "patient"
- La transition try-on → resultat est un moment naturel
- Pas de rupture pendant la manipulation critique (upload, validation)

**Frequency cap** : 1 interstitial max par session (variable `interstitialShownThisSession` dans AdService). Si l'utilisateur fait 10 try-on a la suite, il ne verra qu'**une seule** pub plein ecran. Empeche le "spam".

---

## 🔐 Logique de securite et non-intrusion

### 1. Zero pub sur web

```typescript
private canRun(): boolean {
  if (!Capacitor.isNativePlatform()) return false;  // web = skip
  if (this.premium.isPremium) return false;          // premium = skip
  return true;
}
```

Le site Habileo sur `habileo.com` ne montrera jamais de pub — c'est une vitrine de demo. AdMob est uniquement pour les apps Android/iOS.

### 2. Zero pub si premium

Chaque appel banner/interstitial verifie `premium.isPremium`. Si true → no-op silencieux.

### 3. Activation immediate du premium

Quand l'utilisateur active le premium (achat 1 000 FCFA) :

```typescript
async activatePremium() {
  this.premium.activate();              // localStorage + broadcast
  await this.ads.onPremiumActivated();  // removeBanner() immediat
}
```

Le banner disparait **instantanement**, pas besoin de redemarrer l'app.

### 4. Pas de pub pendant l'upload

Si on affichait un banner pendant l'upload, le user pourrait cliquer accidentellement (zone tactile mobile limitee). Les pages `try-on` et `result` **desactivent explicitement** les banners via `ionViewWillLeave`.

---

## 🗝️ Configuration des IDs

### App ID

Stocke dans [`capacitor.config.ts`](front/capacitor.config.ts) (injecte dans le manifest Android et Info.plist iOS au `cap sync`) :

```typescript
AdMob: {
  appId: 'ca-app-pub-6229155547551594~1030355729',
}
```

### Ad Unit IDs (banner + interstitial)

Varient selon l'environnement — separation dev/prod via les fichiers d'environnement.

**[`environment.ts`](front/src/environments/environment.ts)** (dev) :

```typescript
admob: {
  bannerId: 'ca-app-pub-3940256099942544/6300978111',       // Google TEST ID
  interstitialId: 'ca-app-pub-3940256099942544/1033173712', // Google TEST ID
}
```

**[`environment.prod.ts`](front/src/environments/environment.prod.ts)** (prod) :

```typescript
admob: {
  bannerId: 'ca-app-pub-6229155547551594/6404925159',
  interstitialId: 'ca-app-pub-6229155547551594/1305687894',
}
```

### Pourquoi des IDs de test en dev ?

Google bannit les comptes AdMob qui "cliquent sur leurs propres pubs" (meme accidentellement). Les IDs de test renvoient des pubs factices ("Test Ad") — aucune facturation, aucun risque.

**Regle d'or :** ne **jamais** lancer l'app en mode prod sur ton telephone personnel sans etre sur AdMob Console avec ton device comme "device de test" declare.

---

## 💰 Flux de paiement (a implementer)

Actuellement, `activatePremium()` active localement sans passer par un vrai paiement. Le flux complet sera :

```text
User clique "Activer Premium — 1 000 FCFA"
   ↓
Frontend → POST /api/payment/init  { device_id, amount: 1000 }
   ↓
Backend → appel CinetPay/PayDunya → retourne payment_url
   ↓
Frontend ouvre le formulaire (Orange Money, Wave, MTN, Moov)
   ↓
User paie
   ↓
Callback webhook vers notre backend → notre backend valide
   ↓
Notre backend genere un code de recuperation (ex: "HABI-7G2K-9F3X")
   ↓
Frontend recoit la confirmation + le code
   ↓
PremiumService.activate() + AdService.onPremiumActivated()
   ↓
User voit le code et peut le noter pour une restauration future
```

**A implementer :**

1. Integration CinetPay ou PayDunya (backend)
2. Endpoint `POST /api/payment/init` et webhook `POST /api/payment/callback`
3. Table/stockage des `device_id` premium + codes de recuperation
4. Endpoint `POST /api/payment/recover?code=xxx` pour restaurer le premium sur un autre device
5. UI du code de recuperation apres achat + saisie dans les parametres

---

## 📊 Suivi et optimisation

### Dashboard AdMob

Acceder via [admob.google.com](https://admob.google.com) → ton app Habileo :

| Metric                  | Signification                                          |
| ----------------------- | ------------------------------------------------------ |
| eCPM                    | Gain moyen pour 1000 impressions                       |
| Impressions             | Nombre de fois qu'une pub a ete affichee               |
| Click-through rate      | % de clics sur les pubs (evite > 10%, suspect)         |
| Revenu (EUR/USD)        | Gain accumule (seuil de paiement : $100)               |

### Events a tracker (futur)

- `interstitial_shown` — pour estimer le volume
- `banner_shown`
- `premium_upgrade_initiated`
- `premium_upgrade_completed`

Ajout futur via Firebase Analytics ou event API maison.

---

## 🐞 Depannage

### "Je ne vois aucune pub en dev"

**Normal** si :

- Tu es sur web (Docker compose) → AdMob natif uniquement
- Tu n'as pas encore fait `npx cap sync android` / `npx cap sync ios`
- Tu as declenche le premium via l'UI → les pubs sont cachees

**Verifie :**

```bash
cd front
npx cap sync android      # synchronise le web build + plugin AdMob
npx cap open android       # ouvre Android Studio
# puis Run sur un emulateur
```

### "Pubs reelles en dev = risque de ban"

Si `isTesting: !environment.production` est bien defini dans `ad.service.ts`, les pubs restent factices meme avec tes vrais `adId`. Mais pour etre 100% safe, en dev on utilise les IDs de **test Google** (cf. `environment.ts`).

### "Banner recouvre la tab bar"

Verifie le `margin: 56` dans `ad.service.ts` > `showBanner()`. La tab bar Ionic fait ~56dp de hauteur. Ajuste si besoin.

### "Interstitial ne s'affiche pas la 2eme fois"

Normal : `interstitialShownThisSession = true` apres le 1er affichage. Pour tester plusieurs fois, reset l'app (fermeture + reouverture).

### "Pas de pub meme apres le 1er clic"

Apres un clic sur une pub de test, Google peut mettre un cooldown de 1-2 minutes. Normal, patiente un peu.

---

## 🧪 Tester en local

### Mode dev (web)

```bash
docker compose up --build
# → http://localhost:8080 : pas de pub (normal, web)
```

### Mode natif (Android)

```bash
cd front
npm run build
npx cap sync android
npx cap open android
# Run dans Android Studio sur un emulateur ou telephone USB
```

Le banner apparait sur l'Accueil et la Galerie. L'interstitial se declenche apres un try-on.

---

## 📁 Fichiers impliques

```text
front/
├── capacitor.config.ts                    # App ID AdMob
├── src/
│   ├── environments/
│   │   ├── environment.ts                 # IDs TEST (dev)
│   │   └── environment.prod.ts            # IDs reels (prod)
│   └── app/
│       ├── app.component.ts               # Init AdMob au demarrage
│       ├── services/
│       │   ├── ad.service.ts              # Wrapper AdMob
│       │   └── premium.service.ts         # Statut premium
│       ├── home/home.page.ts              # Banner
│       ├── gallery/gallery.page.ts        # Banner
│       ├── try-on/try-on.page.ts          # Interstitial
│       └── result/result.page.ts          # Activation premium
```

---

## 📚 Ressources

- [Documentation AdMob](https://admob.google.com/home)
- [@capacitor-community/admob (plugin)](https://github.com/capacitor-community/admob)
- [Politique de contenu AdMob](https://support.google.com/adsense/answer/48182)
- [Pricing Mobile Ads par region](https://admob.google.com/home/)
- [Habileo — README principal](./README.md)
