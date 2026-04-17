import { Component, ElementRef, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonContent, IonSelect, IonSelectOption } from '@ionic/angular/standalone';
import { LoadingOverlayComponent } from '../components/loading-overlay/loading-overlay.component';
import { TryOnService } from '../services/tryon.service';

@Component({
  selector: 'app-try-on',
  templateUrl: './try-on.page.html',
  styleUrls: ['./try-on.page.scss'],
  imports: [
    CommonModule,
    FormsModule,
    IonContent,
    IonSelect,
    IonSelectOption,
    LoadingOverlayComponent,
  ],
})
export class TryOnPage {
  userPhoto: string | null = null;
  clothingPhoto: string | null = null;
  clothingZone = '';
  loading = false;

  @ViewChild('userInput') userInput!: ElementRef<HTMLInputElement>;
  @ViewChild('clothingInput') clothingInput!: ElementRef<HTMLInputElement>;

  private userFile: File | null = null;
  private clothingFile: File | null = null;

  constructor(private router: Router, private tryOnService: TryOnService) {}

  onFileSelected(target: 'user' | 'clothing', event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    if (target === 'user') {
      this.userFile = file;
    } else {
      this.clothingFile = file;
    }

    const reader = new FileReader();
    reader.onload = () => {
      if (target === 'user') {
        this.userPhoto = reader.result as string;
      } else {
        this.clothingPhoto = reader.result as string;
      }
    };
    reader.readAsDataURL(file);
  }

  removeClothing(event: Event): void {
    event.stopPropagation();
    this.clothingPhoto = null;
    this.clothingFile = null;
  }

  changeClothing(event: Event): void {
    event.stopPropagation();
    this.clothingInput.nativeElement.click();
  }

  get canGenerate(): boolean {
    return !!this.userPhoto && !!this.clothingPhoto && !!this.clothingZone;
  }

  async generate(): Promise<void> {
    if (!this.canGenerate || !this.userFile || !this.clothingFile) return;
    this.loading = true;

    try {
      const result = await this.tryOnService.generate(this.userFile, this.clothingFile, this.clothingZone);
      this.loading = false;
      if (result.image) {
        this.router.navigate(['/tabs/result'], {
          queryParams: {
            before: this.userPhoto,
            after: result.image,
          },
        });
      }
    } catch {
      this.loading = false;
    }
  }
}
