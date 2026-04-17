import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { IonContent } from '@ionic/angular/standalone';

interface SavedLook {
  id: number;
  image: string;
  label: string;
  date: string;
}

@Component({
  selector: 'app-gallery',
  templateUrl: './gallery.page.html',
  styleUrls: ['./gallery.page.scss'],
  imports: [CommonModule, IonContent, RouterLink],
})
export class GalleryPage {
  savedLooks: SavedLook[] = [
    { id: 1, image: 'assets/fashion-african-1.jpg', label: 'Elegance Ankara', date: '14 Avr' },
    { id: 2, image: 'assets/fashion-african-2.jpg', label: 'Boubou Royal', date: '13 Avr' },
    { id: 3, image: 'assets/fashion-african-3.jpg', label: 'Kaba Dore', date: '12 Avr' },
    { id: 4, image: 'assets/fashion-african-1.jpg', label: 'Wax Chic', date: '11 Avr' },
    { id: 5, image: 'assets/fashion-african-3.jpg', label: 'Soiree Doree', date: '10 Avr' },
    { id: 6, image: 'assets/fashion-african-2.jpg', label: 'Agbada Moderne', date: '9 Avr' },
  ];
}
