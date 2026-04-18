import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

const STORAGE_KEY = 'habileo_premium';

@Injectable({ providedIn: 'root' })
export class PremiumService {
  private premiumSubject = new BehaviorSubject<boolean>(this.readLocal());
  premium$ = this.premiumSubject.asObservable();

  get isPremium(): boolean {
    return this.premiumSubject.value;
  }

  activate(): void {
    localStorage.setItem(STORAGE_KEY, 'true');
    this.premiumSubject.next(true);
  }

  deactivate(): void {
    localStorage.removeItem(STORAGE_KEY);
    this.premiumSubject.next(false);
  }

  private readLocal(): boolean {
    return localStorage.getItem(STORAGE_KEY) === 'true';
  }
}
