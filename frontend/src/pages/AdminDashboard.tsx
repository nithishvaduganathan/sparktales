import React, { useState, useEffect } from 'react';
import { adminService } from '../services/adminService';
import { User, AdminDashboardStats, AuditLog, Group } from '../types';
import './AdminDashboard.css';

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [aiQueries, setAiQueries] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'groups' | 'documents' | 'ai' | 'audit'>('overview');
  const [isLoading, setIsLoading] = useState(true);

  const loadData = async () => {
    try {
      const [statsData, usersData, logsData, groupsData, docsData, aiData] = await Promise.all([
        adminService.getDashboardStats(),
        adminService.listUsers(),
        adminService.getAuditLogs(),
        adminService.listAllGroups(),
        adminService.listAllDocuments(),
        adminService.listAllAIQueries(),
      ]);
      setStats(statsData);
      setUsers(usersData);
      setAuditLogs(logsData.logs);
      setGroups(groupsData.groups);
      setDocuments(docsData);
      setAiQueries(aiData);
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleUserStatus = async (userId: number, currentStatus: boolean) => {
    try {
      await adminService.updateUserStatus(userId, !currentStatus);
      await loadData();
    } catch (err) {
      console.error('Failed to update user status:', err);
    }
  };

  const handleDeleteGroup = async (groupId: number) => {
    if (window.confirm('Are you sure you want to delete this group?')) {
      try {
        await adminService.deleteGroup(groupId);
        await loadData();
      } catch (err) {
        console.error('Failed to delete group:', err);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading admin dashboard...</p>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h1>🛡️ Super Admin Dashboard</h1>
        <p>Monitor and manage the SparkTales LMS platform</p>
      </div>

      <div className="admin-tabs">
        <button className={`tab ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
          Overview
        </button>
        <button className={`tab ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>
          Users
        </button>
        <button className={`tab ${activeTab === 'groups' ? 'active' : ''}`} onClick={() => setActiveTab('groups')}>
          Groups
        </button>
        <button className={`tab ${activeTab === 'documents' ? 'active' : ''}`} onClick={() => setActiveTab('documents')}>
          Documents
        </button>
        <button className={`tab ${activeTab === 'ai' ? 'active' : ''}`} onClick={() => setActiveTab('ai')}>
          AI Queries
        </button>
        <button className={`tab ${activeTab === 'audit' ? 'active' : ''}`} onClick={() => setActiveTab('audit')}>
          Audit Logs
        </button>
      </div>

      <div className="admin-content">
        {activeTab === 'overview' && stats && (
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-icon">👥</span>
              <div className="stat-info">
                <span className="stat-value">{stats.total_users}</span>
                <span className="stat-label">Total Users</span>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">✅</span>
              <div className="stat-info">
                <span className="stat-value">{stats.active_users}</span>
                <span className="stat-label">Active Users</span>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">📄</span>
              <div className="stat-info">
                <span className="stat-value">{stats.total_documents}</span>
                <span className="stat-label">Documents</span>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">👥</span>
              <div className="stat-info">
                <span className="stat-value">{stats.total_groups}</span>
                <span className="stat-label">Groups</span>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">🤖</span>
              <div className="stat-info">
                <span className="stat-value">{stats.total_ai_queries}</span>
                <span className="stat-label">AI Queries</span>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">🔑</span>
              <div className="stat-info">
                <span className="stat-value">{stats.recent_logins}</span>
                <span className="stat-label">Recent Logins (24h)</span>
              </div>
            </div>
            <div className="stat-card warning">
              <span className="stat-icon">⚠️</span>
              <div className="stat-info">
                <span className="stat-value">{stats.failed_logins}</span>
                <span className="stat-label">Failed Logins (24h)</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="admin-table-container">
            <h2>User Management</h2>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td>{user.full_name}</td>
                    <td>{user.email}</td>
                    <td>
                      <span className={`role-badge ${user.role}`}>{user.role}</span>
                    </td>
                    <td>
                      <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                        {user.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td>{new Date(user.created_at).toLocaleDateString()}</td>
                    <td>
                      {user.role !== 'super_admin' && (
                        <button
                          onClick={() => handleToggleUserStatus(user.id, user.is_active)}
                          className={`action-btn ${user.is_active ? 'disable' : 'enable'}`}
                        >
                          {user.is_active ? 'Disable' : 'Enable'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'groups' && (
          <div className="admin-table-container">
            <h2>Group Management</h2>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Members</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {groups.map((group) => (
                  <tr key={group.id}>
                    <td>{group.id}</td>
                    <td>{group.name}</td>
                    <td>{group.group_type}</td>
                    <td>{group.member_count}</td>
                    <td>
                      <span className={`status-badge ${group.is_active ? 'active' : 'inactive'}`}>
                        {group.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>{new Date(group.created_at).toLocaleDateString()}</td>
                    <td>
                      <button onClick={() => handleDeleteGroup(group.id)} className="action-btn delete">
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="admin-table-container">
            <h2>Document Activity</h2>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Owner</th>
                  <th>Type</th>
                  <th>Processed</th>
                  <th>Shared</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td>{doc.id}</td>
                    <td>{doc.title}</td>
                    <td>{doc.owner_email}</td>
                    <td>{doc.file_type}</td>
                    <td>{doc.is_processed ? '✅' : '❌'}</td>
                    <td>{doc.is_shared ? '✅' : '❌'}</td>
                    <td>{new Date(doc.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'ai' && (
          <div className="admin-table-container">
            <h2>AI Query History</h2>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>User</th>
                  <th>Query</th>
                  <th>Response Time</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {aiQueries.map((query) => (
                  <tr key={query.id}>
                    <td>{query.id}</td>
                    <td>{query.user_email}</td>
                    <td className="query-text">{query.query}</td>
                    <td>{query.processing_time}ms</td>
                    <td>{new Date(query.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="admin-table-container">
            <h2>Audit Logs</h2>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Action</th>
                  <th>User ID</th>
                  <th>Resource</th>
                  <th>Success</th>
                  <th>Details</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id}>
                    <td>{log.id}</td>
                    <td>
                      <span className={`action-badge ${log.action}`}>{log.action}</span>
                    </td>
                    <td>{log.user_id || '-'}</td>
                    <td>{log.resource_type ? `${log.resource_type}:${log.resource_id}` : '-'}</td>
                    <td>{log.success ? '✅' : '❌'}</td>
                    <td className="details-text">{log.details || '-'}</td>
                    <td>{new Date(log.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
