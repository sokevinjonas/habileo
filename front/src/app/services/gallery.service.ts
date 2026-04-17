import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { DeviceService } from './device.service';

export interface GalleryItem {
  id: string;
  url: string;
  date: string;
  label: string;
}

export interface GalleryResponse {
  items: GalleryItem[];
  count: number;
}

@Injectable({ providedIn: 'root' })
export class GalleryService {
  constructor(private deviceService: DeviceService) {}

  async fetchGallery(): Promise<GalleryItem[]> {
    const deviceId = await this.deviceService.getDeviceId();
    const url = `${environment.apiUrl}/api/gallery?device_id=${encodeURIComponent(deviceId)}`;

    const response = await fetch(url);
    if (!response.ok) {
      const err = await response.json().catch(() => ({ error: 'Erreur serveur' }));
      throw new Error(err.error || `HTTP ${response.status}`);
    }

    const data: GalleryResponse = await response.json();
    return data.items;
  }

  async deleteItem(publicId: string): Promise<void> {
    const deviceId = await this.deviceService.getDeviceId();
    const url = `${environment.apiUrl}/api/gallery/${encodeURIComponent(publicId)}?device_id=${encodeURIComponent(deviceId)}`;

    const response = await fetch(url, { method: 'DELETE' });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ error: 'Erreur serveur' }));
      throw new Error(err.error || `HTTP ${response.status}`);
    }
  }
}
