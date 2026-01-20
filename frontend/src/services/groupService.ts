import api from './api';
import { Group, GroupDetail, GroupListResponse, GroupInvitation } from '../types';

export const groupService = {
  async createGroup(name: string, description: string, groupType: string): Promise<Group> {
    const response = await api.post('/groups/', {
      name,
      description,
      group_type: groupType,
    });
    return response.data;
  },

  async listGroups(includePrivate = false): Promise<GroupListResponse> {
    const response = await api.get('/groups/', {
      params: { include_private: includePrivate },
    });
    return response.data;
  },

  async listMyGroups(): Promise<GroupListResponse> {
    const response = await api.get('/groups/my-groups');
    return response.data;
  },

  async getGroup(id: number): Promise<GroupDetail> {
    const response = await api.get(`/groups/${id}`);
    return response.data;
  },

  async joinGroup(id: number): Promise<void> {
    await api.post(`/groups/${id}/join`);
  },

  async leaveGroup(id: number): Promise<void> {
    await api.post(`/groups/${id}/leave`);
  },

  async inviteToGroup(groupId: number, inviteeEmail: string): Promise<GroupInvitation> {
    const response = await api.post(`/groups/${groupId}/invite`, {
      invitee_email: inviteeEmail,
    });
    return response.data;
  },

  async getPendingInvitations(): Promise<GroupInvitation[]> {
    const response = await api.get('/groups/invitations/pending');
    return response.data;
  },

  async acceptInvitation(invitationId: number): Promise<void> {
    await api.post(`/groups/invitations/${invitationId}/accept`);
  },

  async rejectInvitation(invitationId: number): Promise<void> {
    await api.post(`/groups/invitations/${invitationId}/reject`);
  },

  async deleteGroup(id: number): Promise<void> {
    await api.delete(`/groups/${id}`);
  },
};
