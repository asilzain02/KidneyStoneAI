export interface ImageResponse {
  id: string; // UUID
  patientId: string;
  fileName: string;
  originalFileName: string;
  fileSize: number;
  contentType: string;
  url: string; 
  status: string;
  uploadDate: string;
}
