import api from './api';
import { User, AuthResponse } from '../types';

export const authService = {
  async register(email: string, password: string, fullName: string): Promise<User> {
    const response = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await api.post('/auth/login', {
      email,
      password,
    });
    return response.data;
  },

  async getMe(): Promise<User> {
    const response = await api.get('/auth/me');
    return response.data;
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  },
};
