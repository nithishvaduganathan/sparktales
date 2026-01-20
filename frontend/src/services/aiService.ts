import api from './api';
import { AIQueryResponse, AIQueryHistoryResponse } from '../types';

export const aiService = {
  async askQuestion(query: string, documentIds?: number[]): Promise<AIQueryResponse> {
    const response = await api.post('/ai/query', {
      query,
      document_ids: documentIds,
    });
    return response.data;
  },

  async getQueryHistory(skip = 0, limit = 20): Promise<AIQueryHistoryResponse> {
    const response = await api.get('/ai/history', {
      params: { skip, limit },
    });
    return response.data;
  },

  async getQuery(id: number): Promise<AIQueryResponse> {
    const response = await api.get(`/ai/query/${id}`);
    return response.data;
  },
};
