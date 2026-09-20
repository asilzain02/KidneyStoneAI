import { apiClient } from '@/services/http/apiClient';
import { AuthResponse, LoginCredentials, UserResponse } from '../types';

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
    return response as unknown as AuthResponse;
  },
  
  logout: () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    window.location.href = '/login';
  },

  getProfile: async (): Promise<UserResponse> => {
    const response = await apiClient.get<UserResponse>('/auth/profile');
    return response as unknown as UserResponse;
  },

  getUsers: async (): Promise<UserResponse[]> => {
    const response = await apiClient.get<UserResponse[]>('/auth/users');
    return (response as unknown as UserResponse[]) || [];
  },

  createUser: async (userData: any): Promise<UserResponse> => {
    const response = await apiClient.post<UserResponse>('/auth/users', userData);
    return response as unknown as UserResponse;
  },

  deleteUser: async (id: string): Promise<void> => {
    await apiClient.delete(`/auth/users/${id}`);
  },
};
