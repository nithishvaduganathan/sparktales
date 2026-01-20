import api from './api';
import { Document, DocumentListResponse } from '../types';

export const documentService = {
  async uploadDocument(title: string, file: File, groupId?: number): Promise<Document> {
    const formData = new FormData();
    formData.append('title', title);
    formData.append('file', file);
    if (groupId) {
      formData.append('group_id', groupId.toString());
    }
    
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async listDocuments(skip = 0, limit = 20): Promise<DocumentListResponse> {
    const response = await api.get('/documents/', {
      params: { skip, limit },
    });
    return response.data;
  },

  async listSharedDocuments(skip = 0, limit = 20): Promise<DocumentListResponse> {
    const response = await api.get('/documents/shared', {
      params: { skip, limit },
    });
    return response.data;
  },

  async getDocument(id: number): Promise<Document> {
    const response = await api.get(`/documents/${id}`);
    return response.data;
  },

  async updateDocument(id: number, data: { title?: string; is_shared?: boolean }): Promise<Document> {
    const response = await api.put(`/documents/${id}`, data);
    return response.data;
  },

  async deleteDocument(id: number): Promise<void> {
    await api.delete(`/documents/${id}`);
  },
};
