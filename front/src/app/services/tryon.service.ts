import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { DeviceService } from './device.service';

export interface TryOnResult {
  image?: string;
  id?: string;
  error?: string;
  field?: string;
}

@Injectable({ providedIn: 'root' })
export class TryOnService {
  constructor(private deviceService: DeviceService) {}

  async generate(userFile: File, clothFile: File, zone: string, garmentDesc = ''): Promise<TryOnResult> {
    const deviceId = await this.deviceService.getDeviceId();

    const formData = new FormData();
    formData.append('user', userFile);
    formData.append('cloth', clothFile);
    formData.append('zone', zone);
    formData.append('device_id', deviceId);
    if (garmentDesc) {
      formData.append('garment_desc', garmentDesc);
    }

    const response = await fetch(`${environment.apiUrl}/api/try-on`, {
      method: 'POST',
      body: formData,
    });

    return response.json();
  }
}
