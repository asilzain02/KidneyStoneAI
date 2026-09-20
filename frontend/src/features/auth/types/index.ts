export interface UserResponse {
  id: string; // usually UUID string
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  role: string;
  permissions?: string[];
  status?: string;
  isVerified?: boolean;
  createdAt?: string;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  user: UserResponse;
}

export interface LoginCredentials {
  email: string; // The Java backend might use email or username based on configuration.
  password: string;
}
