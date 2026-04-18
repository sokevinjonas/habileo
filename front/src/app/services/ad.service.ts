import { Injectable } from '@angular/core';
import { Capacitor } from '@capacitor/core';
import {
  AdMob,
  AdmobConsentStatus,
  BannerAdOptions,
  BannerAdPosition,
  BannerAdSize,
  AdOptions,
} from '@capacitor-community/admob';
import { environment } from '../../environments/environment';
import { PremiumService } from './premium.service';

@Injectable({ providedIn: 'root' })
export class AdService {
  private initialized = false;
  private bannerVisible = false;
  private interstitialShownThisSession = false;

  constructor(private premium: PremiumService) {}

  // ─── Lifecycle ──────────────────────────────────────────────

  /** Appele une seule fois au demarrage de l'app. */
  async init(): Promise<void> {
    if (this.initialized) return;
    if (!this.canRun()) return;

    try {
      await AdMob.initialize({
        testingDevices: [], // remplir avec les IDs de tes devices de test si besoin
        initializeForTesting: !environment.production,
      });

      // GDPR consent (important pour l'Europe, optionnel en Afrique mais recommande)
      const consent = await AdMob.requestConsentInfo();
      if (
        consent.status === AdmobConsentStatus.REQUIRED ||
        consent.status === AdmobConsentStatus.UNKNOWN
      ) {
        await AdMob.showConsentForm().catch(() => {/* user fermé le form */});
      }

      this.initialized = true;
    } catch (err) {
      console.warn('[AdService] init failed:', err);
    }
  }

  // ─── Banner ─────────────────────────────────────────────────

  async showBanner(): Promise<void> {
    if (!this.canRun() || this.bannerVisible) return;

    const options: BannerAdOptions = {
      adId: environment.admob.bannerId,
      adSize: BannerAdSize.ADAPTIVE_BANNER,
      position: BannerAdPosition.BOTTOM_CENTER,
      margin: 56, // au-dessus de la tab bar Ionic
      isTesting: !environment.production,
    };

    try {
      await AdMob.showBanner(options);
      this.bannerVisible = true;
    } catch (err) {
      console.warn('[AdService] showBanner failed:', err);
    }
  }

  async hideBanner(): Promise<void> {
    if (!this.canRun() || !this.bannerVisible) return;
    try {
      await AdMob.hideBanner();
      this.bannerVisible = false;
    } catch (err) {
      console.warn('[AdService] hideBanner failed:', err);
    }
  }

  async removeBanner(): Promise<void> {
    if (!this.canRun()) return;
    try {
      await AdMob.removeBanner();
      this.bannerVisible = false;
    } catch {
      // ignore
    }
  }

  // ─── Interstitial ───────────────────────────────────────────

  /**
   * Charge et affiche un interstitial.
   * Limite a 1 affichage par session pour ne pas saturer l'user.
   */
  async showInterstitial(): Promise<void> {
    if (!this.canRun()) return;
    if (this.interstitialShownThisSession) return;

    const options: AdOptions = {
      adId: environment.admob.interstitialId,
      isTesting: !environment.production,
    };

    try {
      await AdMob.prepareInterstitial(options);
      await AdMob.showInterstitial();
      this.interstitialShownThisSession = true;
    } catch (err) {
      console.warn('[AdService] showInterstitial failed:', err);
    }
  }

  /** A appeler si le user active le premium pour cacher les pubs immediatement. */
  async onPremiumActivated(): Promise<void> {
    await this.removeBanner();
  }

  // ─── Helpers ────────────────────────────────────────────────

  private canRun(): boolean {
    // Pas de pub : en environnement web (AdMob natif uniquement) ou si user premium
    if (!Capacitor.isNativePlatform()) return false;
    if (this.premium.isPremium) return false;
    return true;
  }
}
