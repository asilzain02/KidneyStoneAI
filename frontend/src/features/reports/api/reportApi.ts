import { apiClient } from '@/services/http/apiClient';
import { ReportResponse, GenerateReportRequest } from '../types';

export const reportApi = {
  getReports: async (): Promise<any[]> => {
    const response = await apiClient.get<any>('/reports');
    const rootData = response.data || response;
    if (Array.isArray(rootData)) return rootData;
    if (rootData && Array.isArray(rootData.content)) return rootData.content;
    return [];
  },

  getReportDetail: async (diagnosisId: string): Promise<ReportResponse> => {
    const response = await apiClient.get<ReportResponse>(`/diagnoses/${diagnosisId}`);
    return response as unknown as ReportResponse;
  },

  generateReport: async (data: GenerateReportRequest): Promise<ReportResponse> => {
    const response = await apiClient.post<ReportResponse>('/reports/generate', data);
    return response as unknown as ReportResponse;
  },
  
  getReportPdf: async (diagnosisId: string): Promise<Blob> => {
    const response = await apiClient.get(`/reports/${diagnosisId}/pdf`, { responseType: 'blob' });
    return response as unknown as Blob;
  }
};
