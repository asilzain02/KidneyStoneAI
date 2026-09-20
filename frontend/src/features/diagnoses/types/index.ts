export interface DiagnosisResponse {
  id: string; // UUID
  imageId: string;
  patientId: string;
  inferenceId: string;
  predictedClass: string;
  confidence: number;
  stoneDetected: boolean;
  stoneAreaPixels: number;
  coverageRatio: number;
  heatmapUrl: string;
  overlayUrl: string;
  xaiMethod: string;
  consistencyStatus: 'CONSISTENT' | 'PARTIAL_DISAGREEMENT' | 'DISAGREEMENT' | string;
  consistencyMessage: string;
  classificationModel: string;
  segmentationModel: string;
  processingTimeMs: number;
  device: string;
  severityLevel: string;
  severityReason: string;
  treatmentCategory: string;
  treatmentRecommendation: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | string;
  createdAt: string;
  comparisonImageUrl: string | null;
}

export interface CreateDiagnosisRequest {
  imageId: string;
  patientId: string;
}
