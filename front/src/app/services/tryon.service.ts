import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

export interface TryOnResult {
  image?: string;
  error?: string;
  field?: string;
}

@Injectable({ providedIn: 'root' })
export class TryOnService {

  async generate(userFile: File, clothFile: File, zone: string, garmentDesc = ''): Promise<TryOnResult> {
    const formData = new FormData();
    formData.append('user', userFile);
    formData.append('cloth', clothFile);
    formData.append('zone', zone);
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
