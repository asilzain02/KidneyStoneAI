import { apiClient } from '@/services/http/apiClient';
import { DiagnosisResponse, CreateDiagnosisRequest } from '../types';

export const diagnosisApi = {
  createDiagnosis: async (data: CreateDiagnosisRequest): Promise<DiagnosisResponse> => {
    return apiClient.post('/diagnoses', data);
  },

  getDiagnosis: async (id: string): Promise<DiagnosisResponse> => {
    return apiClient.get(`/diagnoses/${id}`);
  },

  getDiagnoses: async (): Promise<DiagnosisResponse[]> => {
    const response: any = await apiClient.get('/diagnoses');
    if (response && Array.isArray(response.content)) {
      return response.content;
    }
    if (Array.isArray(response)) {
      return response;
    }
    return [];
  },

  getComparisonImage: async (id: string): Promise<Blob> => {
    const response = await apiClient.get<Blob>(`/diagnoses/${id}/comparison`, { responseType: 'blob' });
    return response.data || response;
  },

  getSegmentationImage: async (id: string): Promise<Blob> => {
    const response = await apiClient.get<Blob>(`/diagnoses/${id}/segmentation`, { responseType: 'blob' });
    return response.data || response;
  },

  getGradCamImage: async (id: string): Promise<Blob> => {
    const response = await apiClient.get<Blob>(`/diagnoses/${id}/gradcam`, { responseType: 'blob' });
    return response.data || response;
  }
};
