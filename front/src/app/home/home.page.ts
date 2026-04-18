import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { IonContent } from '@ionic/angular/standalone';
import { AdService } from '../services/ad.service';

@Component({
  selector: 'app-home',
  templateUrl: './home.page.html',
  styleUrls: ['./home.page.scss'],
  imports: [IonContent, RouterLink],
})
export class HomePage {
  constructor(private ads: AdService) {}

  steps = [
    { num: '1', title: 'Uploadez votre photo', desc: 'Une photo en pied bien nette donne les meilleurs resultats' },
    { num: '2', title: 'Choisissez une tenue', desc: "Uploadez n'importe quelle image de vetement" },
    { num: '3', title: 'Voyez la magie', desc: "L'IA genere votre nouveau look instantanement" },
  ];

  transformations = [
    { image: 'assets/fashion-african-1.jpg', label: 'Elegance Ankara', style: 'Robe en Wax' },
    { image: 'assets/fashion-african-2.jpg', label: 'Boubou Royal', style: 'Agbada Indigo' },
    { image: 'assets/fashion-african-3.jpg', label: 'Kaba Dore', style: 'Kaba Brode' },
  ];

  async ionViewDidEnter(): Promise<void> {
    await this.ads.showBanner();
  }

  async ionViewWillLeave(): Promise<void> {
    await this.ads.hideBanner();
  }
}
