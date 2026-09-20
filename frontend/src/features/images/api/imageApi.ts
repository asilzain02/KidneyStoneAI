import { apiClient } from '@/services/http/apiClient';
import { ImageResponse } from '../types';

export const imageApi = {
  uploadImage: async (patientId: string, file: File, fileName?: string): Promise<ImageResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (fileName && fileName.trim() !== '') {
      formData.append('fileName', fileName);
    }

    return apiClient.post(`/images/upload/${patientId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  getImagesByPatient: async (patientId: string): Promise<ImageResponse[]> => {
    const response: any = await apiClient.get(`/images/patient/${patientId}`);
    if (response && Array.isArray(response.content)) {
      return response.content;
    }
    if (Array.isArray(response)) {
      return response;
    }
    return [];
  },

  getImage: async (id: string): Promise<ImageResponse> => {
    return apiClient.get(`/images/${id}`);
  }
};
