import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { IonContent, IonModal } from '@ionic/angular/standalone';

@Component({
  selector: 'app-result',
  templateUrl: './result.page.html',
  styleUrls: ['./result.page.scss'],
  imports: [IonContent, IonModal, RouterLink],
})
export class ResultPage implements OnInit {
  sliderPos = 50;
  saved = false;
  showPremium = false;
  isPremium = false;

  beforeImage = 'assets/fashion-african-1.jpg';
  afterImage = 'assets/fashion-african-3.jpg';

  constructor(private route: ActivatedRoute) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      if (params['before']) this.beforeImage = params['before'];
      if (params['after']) this.afterImage = params['after'];
    });
  }

  onSliderMove(event: MouseEvent | TouchEvent): void {
    const el = (event.currentTarget as HTMLElement);
    const rect = el.getBoundingClientRect();
    const clientX = 'touches' in event ? event.touches[0].clientX : event.clientX;
    this.sliderPos = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
  }

  premiumAction(action: () => void): void {
    if (this.isPremium) {
      action();
    } else {
      this.showPremium = true;
    }
  }

  activatePremium(): void {
    this.isPremium = true;
    this.showPremium = false;
  }

  toggleSave(): void {
    this.saved = !this.saved;
  }

  download(): void {
    // TODO: implement download
  }

  share(): void {
    // TODO: implement share
  }
}
