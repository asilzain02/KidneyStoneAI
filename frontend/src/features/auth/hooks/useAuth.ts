import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { authApi } from '../api/authApi';
import { LoginCredentials } from '../types';

export const useAuth = () => {
  const navigate = useNavigate();

  const loginMutation = useMutation({
    mutationFn: (credentials: LoginCredentials) => authApi.login(credentials),
    onSuccess: (data) => {
      localStorage.setItem('accessToken', data.accessToken);
      if (data.refreshToken) {
        localStorage.setItem('refreshToken', data.refreshToken);
      }
      toast.success('Login successful');
      navigate('/dashboard');
    },
    onError: (error: any) => {
      let message = 'Unable to complete sign-in. Please try again.';
      if (error.response) {
        if (error.response.status === 401 || error.response.status === 403) {
          message = 'Invalid email or password.';
        } else if (error.response.status >= 500) {
          message = 'Authentication service error. Please try again.';
        } else if (error.response.data?.error?.details) {
          message = error.response.data.error.details;
        }
      }
      toast.error(message);
    },
  });

  const logout = () => {
    authApi.logout();
  };

  return {
    login: loginMutation.mutate,
    isLoggingIn: loginMutation.isPending,
    logout,
    isAuthenticated: !!localStorage.getItem('accessToken'),
  };
};
