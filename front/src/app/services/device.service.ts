import { Injectable } from '@angular/core';
import { Device } from '@capacitor/device';

const STORAGE_KEY = 'habileo_device_id';

@Injectable({ providedIn: 'root' })
export class DeviceService {
  private cached: string | null = null;

  async getDeviceId(): Promise<string> {
    if (this.cached) return this.cached;

    // Try Capacitor first (works on native + web)
    try {
      const info = await Device.getId();
      if (info?.identifier) {
        this.cached = info.identifier;
        localStorage.setItem(STORAGE_KEY, info.identifier);
        return this.cached;
      }
    } catch {
      // ignore, fall through to localStorage
    }

    // Fallback: UUID persisted in localStorage
    let id = localStorage.getItem(STORAGE_KEY);
    if (!id) {
      id = this.generateUuid();
      localStorage.setItem(STORAGE_KEY, id);
    }
    this.cached = id;
    return id;
  }

  private generateUuid(): string {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    // Simple fallback
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }
}
