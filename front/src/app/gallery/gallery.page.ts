import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { IonContent, IonRefresher, IonRefresherContent, IonSpinner } from '@ionic/angular/standalone';
import { GalleryService, GalleryItem } from '../services/gallery.service';
import { AdService } from '../services/ad.service';

type LoadState = 'idle' | 'loading' | 'ready' | 'error' | 'offline' | 'empty';

@Component({
  selector: 'app-gallery',
  templateUrl: './gallery.page.html',
  styleUrls: ['./gallery.page.scss'],
  imports: [IonContent, IonRefresher, IonRefresherContent, IonSpinner, RouterLink],
})
export class GalleryPage implements OnInit {
  items: GalleryItem[] = [];
  state: LoadState = 'idle';
  errorMessage = '';

  constructor(private galleryService: GalleryService, private ads: AdService) {}

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  async ionViewWillEnter(): Promise<void> {
    // Refresh quand on revient sur la page
    if (this.state !== 'loading') {
      await this.load();
    }
  }

  async ionViewDidEnter(): Promise<void> {
    await this.ads.showBanner();
  }

  async ionViewWillLeave(): Promise<void> {
    await this.ads.hideBanner();
  }

  async load(): Promise<void> {
    if (!navigator.onLine) {
      this.state = 'offline';
      return;
    }

    this.state = 'loading';
    this.errorMessage = '';

    try {
      this.items = await this.galleryService.fetchGallery();
      this.state = this.items.length === 0 ? 'empty' : 'ready';
    } catch (e: any) {
      this.errorMessage = e?.message || 'Erreur inconnue';
      this.state = 'error';
    }
  }

  async handleRefresh(event: any): Promise<void> {
    await this.load();
    event.target.complete();
  }

  formatDate(iso: string): string {
    if (!iso) return '';
    const d = new Date(iso);
    const months = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aout', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${d.getDate()} ${months[d.getMonth()]}`;
  }

  truncateLabel(label: string, max = 24): string {
    if (!label) return 'Look sans nom';
    return label.length > max ? label.slice(0, max).trim() + '...' : label;
  }
}
