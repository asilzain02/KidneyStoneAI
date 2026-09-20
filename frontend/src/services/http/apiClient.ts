import axios from 'axios';

// Since we setup standard vite proxy, /api maps to backend gateway
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds (AI inference can take up to 30s)
});

apiClient.interceptors.request.use(
  (config) => {
    // API Observability LOGGING
    if (import.meta.env.DEV) {
      console.log(`[API REQUEST]\nMETHOD: ${config.method?.toUpperCase()}\nURL: ${config.url}`);
    }

    // We will store our token in localStorage for simplicity, but could be adapted easily.
    const token = localStorage.getItem('accessToken');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`[API RESPONSE]\nMETHOD: ${response.config.method?.toUpperCase()}\nURL: ${response.config.url}\nSTATUS: ${response.status}\nBODY:`, response.data);
    }
    // Try to safely extract 'data' if it's an ApiResponse wrapper, else return the raw body
    if (response.data && typeof response.data === 'object' && 'status' in response.data && 'data' in response.data) {
       return response.data.data;
    }
    return response.data;
  },
  (error) => {
    if (import.meta.env.DEV) {
      const { config, response } = error;
      console.error(
        `[API ERROR]\nMETHOD: ${config?.method?.toUpperCase()}\nURL: ${config?.url}\nSTATUS: ${response?.status || 'Network Error'}\nBACKEND MESSAGE:`,
        response?.data?.error || response?.data?.message || error.message,
        '\nRESPONSE BODY:',
        response?.data
      );
    }

    if (error.response?.status === 401) {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      // Redirect to login - in a more rigorous setup this could trigger an event
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
