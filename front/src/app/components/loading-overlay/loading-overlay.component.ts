import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-overlay',
  templateUrl: './loading-overlay.component.html',
  styleUrls: ['./loading-overlay.component.scss'],
  imports: [CommonModule],
})
export class LoadingOverlayComponent implements OnInit, OnDestroy {
  messages = [
    'Analyse de votre photo...',
    'Cartographie des contours du corps...',
    'Ajustement de la tenue...',
    'Touches finales...',
    'Creation de votre look...',
  ];

  currentMessage = this.messages[0];
  progress = 0;

  private msgInterval: ReturnType<typeof setInterval> | null = null;
  private progInterval: ReturnType<typeof setInterval> | null = null;
  private msgIndex = 0;

  ngOnInit(): void {
    this.msgInterval = setInterval(() => {
      this.msgIndex = (this.msgIndex + 1) % this.messages.length;
      this.currentMessage = this.messages[this.msgIndex];
    }, 3000);

    this.progInterval = setInterval(() => {
      this.progress = Math.min(this.progress + Math.random() * 8, 95);
    }, 500);
  }

  ngOnDestroy(): void {
    if (this.msgInterval) clearInterval(this.msgInterval);
    if (this.progInterval) clearInterval(this.progInterval);
  }
}
