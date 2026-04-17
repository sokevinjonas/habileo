import { Component, OnInit, OnDestroy } from '@angular/core';

@Component({
  selector: 'app-loading-overlay',
  templateUrl: './loading-overlay.component.html',
  styleUrls: ['./loading-overlay.component.scss'],
})
export class LoadingOverlayComponent implements OnInit, OnDestroy {
  messages = [
    'Nettoyage de l\'image du vetement...',
    'Suppression de l\'arriere-plan...',
    'Isolation du vetement...',
    'Analyse de votre morphologie...',
    'Cartographie des contours du corps...',
    'Application du vetement...',
    'Ajustement des details...',
    'Touches finales...',
    'Creation de votre look...',
  ];

  currentMessage = this.messages[0];
  currentStep = 'Etape 1/2 — Preparation du vetement';
  progress = 0;

  private msgInterval: ReturnType<typeof setInterval> | null = null;
  private progInterval: ReturnType<typeof setInterval> | null = null;
  private stepInterval: ReturnType<typeof setInterval> | null = null;
  private msgIndex = 0;

  ngOnInit(): void {
    this.msgInterval = setInterval(() => {
      this.msgIndex = (this.msgIndex + 1) % this.messages.length;
      this.currentMessage = this.messages[this.msgIndex];
    }, 3000);

    this.progInterval = setInterval(() => {
      this.progress = Math.min(this.progress + Math.random() * 5, 95);
    }, 600);

    // Switch step label at ~45%
    this.stepInterval = setInterval(() => {
      if (this.progress > 40) {
        this.currentStep = 'Etape 2/2 — Essayage virtuel IA';
        if (this.stepInterval) {
          clearInterval(this.stepInterval);
          this.stepInterval = null;
        }
      }
    }, 1000);
  }

  ngOnDestroy(): void {
    if (this.msgInterval) clearInterval(this.msgInterval);
    if (this.progInterval) clearInterval(this.progInterval);
    if (this.stepInterval) clearInterval(this.stepInterval);
  }
}
