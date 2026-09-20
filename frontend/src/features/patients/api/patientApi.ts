import { apiClient } from '@/services/http/apiClient';
import { Patient, CreatePatientRequest } from '../types';

export const patientApi = {
  getPatients: async (): Promise<Patient[]> => {
    const response: any = await apiClient.get('/patients');
    if (response && Array.isArray(response.content)) {
      return response.content;
    }
    if (Array.isArray(response)) {
      return response;
    }
    return [];
  },

  getPatient: async (id: string): Promise<Patient> => {
    return apiClient.get(`/patients/${id}`);
  },

  createPatient: async (data: CreatePatientRequest): Promise<Patient> => {
    return apiClient.post('/patients', data);
  },
};
