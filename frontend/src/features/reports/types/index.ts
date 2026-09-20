export interface ReportResponse {
  id: string; // UUID
  diagnosisId: string;
  patientId: string;
  structuredReport?: string;
  reportContent?: string;
  format: string; // PDF or MD or HTML maybe
  status: string;
  generatedAt: string;
  downloadUrl: string;
}

export interface GenerateReportRequest {
  diagnosisId: string;
  patientId: string;
}
