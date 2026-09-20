export interface ApiResponse<T> {
  status: 'SUCCESS' | 'ERROR';
  message: string;
  timestamp: string;
  data: T;
  error?: {
    code: string;
    details: string;
  };
}
