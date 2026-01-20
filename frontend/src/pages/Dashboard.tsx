import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { documentService } from '../services/documentService';
import { groupService } from '../services/groupService';
import { Document, Group } from '../types';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [recentDocuments, setRecentDocuments] = useState<Document[]>([]);
  const [myGroups, setMyGroups] = useState<Group[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [docsResponse, groupsResponse] = await Promise.all([
          documentService.listDocuments(0, 5),
          groupService.listMyGroups(),
        ]);
        setRecentDocuments(docsResponse.documents);
        setMyGroups(groupsResponse.groups);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, []);

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Welcome, {user?.full_name}!</h1>
        <p>Here's an overview of your learning journey</p>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-header">
            <h2>Quick Actions</h2>
          </div>
          <div className="quick-actions">
            <Link to="/documents" className="action-btn">
              <span className="action-icon">📄</span>
              <span>Upload Document</span>
            </Link>
            <Link to="/ai-chat" className="action-btn">
              <span className="action-icon">🤖</span>
              <span>Ask AI</span>
            </Link>
            <Link to="/groups" className="action-btn">
              <span className="action-icon">👥</span>
              <span>Join Groups</span>
            </Link>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-header">
            <h2>Recent Documents</h2>
            <Link to="/documents" className="view-all">View All</Link>
          </div>
          {recentDocuments.length > 0 ? (
            <ul className="document-list">
              {recentDocuments.map((doc) => (
                <li key={doc.id} className="document-item">
                  <span className="doc-icon">📄</span>
                  <div className="doc-info">
                    <span className="doc-title">{doc.title}</span>
                    <span className="doc-date">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-message">No documents uploaded yet.</p>
          )}
        </div>

        <div className="dashboard-card">
          <div className="card-header">
            <h2>My Groups</h2>
            <Link to="/groups" className="view-all">View All</Link>
          </div>
          {myGroups.length > 0 ? (
            <ul className="group-list">
              {myGroups.map((group) => (
                <li key={group.id} className="group-item">
                  <Link to={`/groups/${group.id}`}>
                    <span className="group-icon">
                      {group.group_type === 'private' ? '🔒' : '🌐'}
                    </span>
                    <div className="group-info">
                      <span className="group-name">{group.name}</span>
                      <span className="group-members">
                        {group.member_count} members
                      </span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-message">You haven't joined any groups yet.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
