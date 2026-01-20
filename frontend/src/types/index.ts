// API types
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface Document {
  id: number;
  title: string;
  filename: string;
  file_type: string;
  file_size: number;
  is_processed: boolean;
  is_shared: boolean;
  owner_id: number;
  group_id?: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

export interface Group {
  id: number;
  name: string;
  description?: string;
  group_type: string;
  is_active: boolean;
  owner_id: number;
  created_at: string;
  member_count: number;
}

export interface GroupMember {
  id: number;
  user_id: number;
  full_name: string;
  email: string;
  role: string;
  joined_at: string;
}

export interface GroupDetail extends Group {
  members: GroupMember[];
}

export interface GroupListResponse {
  groups: Group[];
  total: number;
}

export interface Message {
  id: number;
  content: string;
  author_id: number;
  author?: {
    id: number;
    full_name: string;
    email: string;
  };
  group_id: number;
  created_at: string;
  updated_at: string;
}

export interface MessageListResponse {
  messages: Message[];
  total: number;
}

export interface AIQueryResponse {
  id: number;
  query: string;
  response: string;
  document_ids?: string;
  processing_time?: number;
  created_at: string;
}

export interface AIQueryHistoryResponse {
  queries: AIQueryResponse[];
  total: number;
}

export interface GroupInvitation {
  id: number;
  group_id: number;
  group_name: string;
  inviter_name: string;
  status: string;
  created_at: string;
}

export interface AdminDashboardStats {
  total_users: number;
  active_users: number;
  total_documents: number;
  total_groups: number;
  total_ai_queries: number;
  recent_logins: number;
  failed_logins: number;
}

export interface AuditLog {
  id: number;
  user_id?: number;
  action: string;
  resource_type?: string;
  resource_id?: number;
  details?: string;
  ip_address?: string;
  success: number;
  created_at: string;
}
