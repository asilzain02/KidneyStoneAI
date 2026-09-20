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

  getReport: async (id: string): Promise<ReportResponse> => {
    const response = await apiClient.get<ReportResponse>(`/diagnoses/${id}/report`);
    return response as unknown as ReportResponse;
  },

  generateReport: async (data: GenerateReportRequest): Promise<ReportResponse> => {
    const response = await apiClient.post<ReportResponse>('/reports/generate', data);
    return response as unknown as ReportResponse;
  },
  
  downloadReport: async (id: string): Promise<Blob> => {
    // Because this returns a blob (e.g. PDF), we might not want it unwrapped as JSON {status, data}.
    // If the java backend returns raw byte[], this needs standard axios bypass.
    // The architecture returns JSON from /diagnoses/{id}/report, but UI expects a download.
    const response = await apiClient.get(`/diagnoses/${id}/report`, { responseType: 'blob' });
    return response as unknown as Blob;
  }
};
