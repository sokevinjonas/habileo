import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.habileo.app',
  appName: 'Habileo',
  webDir: 'www',
  plugins: {
    AdMob: {
      appId: 'ca-app-pub-6229155547551594~1030355729',
      // Les IDs d'unites publicitaires sont dans environment.ts (banner, interstitial)
    },
  },
};

export default config;
