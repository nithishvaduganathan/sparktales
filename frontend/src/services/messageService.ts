import api from './api';
import { Message, MessageListResponse } from '../types';

export const messageService = {
  async listMessages(groupId: number, skip = 0, limit = 50): Promise<MessageListResponse> {
    const response = await api.get(`/groups/${groupId}/messages/`, {
      params: { skip, limit },
    });
    return response.data;
  },

  async createMessage(groupId: number, content: string): Promise<Message> {
    const response = await api.post(`/groups/${groupId}/messages/`, {
      content,
    });
    return response.data;
  },

  async updateMessage(groupId: number, messageId: number, content: string): Promise<Message> {
    const response = await api.put(`/groups/${groupId}/messages/${messageId}`, {
      content,
    });
    return response.data;
  },

  async deleteMessage(groupId: number, messageId: number): Promise<void> {
    await api.delete(`/groups/${groupId}/messages/${messageId}`);
  },
};
