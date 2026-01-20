import api from './api';
import { User, AdminDashboardStats, AuditLog, GroupListResponse } from '../types';

export const adminService = {
  async getDashboardStats(): Promise<AdminDashboardStats> {
    const response = await api.get('/admin/dashboard');
    return response.data;
  },

  async listUsers(skip = 0, limit = 50): Promise<User[]> {
    const response = await api.get('/admin/users', {
      params: { skip, limit },
    });
    return response.data;
  },

  async getUser(id: number): Promise<User> {
    const response = await api.get(`/admin/users/${id}`);
    return response.data;
  },

  async updateUserStatus(id: number, isActive: boolean): Promise<User> {
    const response = await api.put(`/admin/users/${id}/status`, {
      is_active: isActive,
    });
    return response.data;
  },

  async getAuditLogs(skip = 0, limit = 50, action?: string, userId?: number): Promise<{ logs: AuditLog[]; total: number }> {
    const response = await api.get('/admin/audit-logs', {
      params: { skip, limit, action, user_id: userId },
    });
    return response.data;
  },

  async listAllGroups(skip = 0, limit = 50): Promise<GroupListResponse> {
    const response = await api.get('/admin/groups', {
      params: { skip, limit },
    });
    return response.data;
  },

  async deleteGroup(id: number): Promise<void> {
    await api.delete(`/admin/groups/${id}`);
  },

  async listAllDocuments(skip = 0, limit = 50): Promise<any[]> {
    const response = await api.get('/admin/documents', {
      params: { skip, limit },
    });
    return response.data;
  },

  async listAllAIQueries(skip = 0, limit = 50): Promise<any[]> {
    const response = await api.get('/admin/ai-queries', {
      params: { skip, limit },
    });
    return response.data;
  },
};
