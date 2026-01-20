import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { groupService } from '../services/groupService';
import { messageService } from '../services/messageService';
import { useAuth } from '../contexts/AuthContext';
import { GroupDetail, Message } from '../types';
import './GroupDetail.css';

const GroupDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [group, setGroup] = useState<GroupDetail | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteError, setInviteError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const groupId = parseInt(id || '0');

  const loadData = async () => {
    try {
      const [groupData, messagesData] = await Promise.all([
        groupService.getGroup(groupId),
        messageService.listMessages(groupId),
      ]);
      setGroup(groupData);
      setMessages(messagesData.messages.reverse());
    } catch (err) {
      console.error('Failed to load group:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (groupId) {
      loadData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [groupId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    try {
      const message = await messageService.createMessage(groupId, newMessage);
      setMessages([...messages, message]);
      setNewMessage('');
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteError('');

    try {
      await groupService.inviteToGroup(groupId, inviteEmail);
      setInviteEmail('');
      setShowInvite(false);
      alert('Invitation sent successfully!');
    } catch (err: any) {
      setInviteError(err.response?.data?.detail || 'Failed to send invitation');
    }
  };

  const isAdmin = group?.members.some(
    (m) => m.user_id === user?.id && m.role === 'admin'
  );

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading group...</p>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="error-container">
        <h2>Group not found</h2>
        <Link to="/groups">Back to Groups</Link>
      </div>
    );
  }

  return (
    <div className="group-detail-page">
      <div className="group-sidebar">
        <Link to="/groups" className="back-link">← Back to Groups</Link>
        
        <div className="group-info">
          <div className="group-type-icon">
            {group.group_type === 'private' ? '🔒' : '🌐'}
          </div>
          <h2>{group.name}</h2>
          <p className="group-description">{group.description}</p>
        </div>

        <div className="members-section">
          <div className="members-header">
            <h3>Members ({group.members.length})</h3>
            {isAdmin && group.group_type === 'private' && (
              <button onClick={() => setShowInvite(true)} className="invite-btn">
                Invite
              </button>
            )}
          </div>
          <ul className="members-list">
            {group.members.map((member) => (
              <li key={member.id} className="member-item">
                <span className="member-avatar">
                  {member.full_name.charAt(0).toUpperCase()}
                </span>
                <div className="member-info">
                  <span className="member-name">{member.full_name}</span>
                  {member.role === 'admin' && (
                    <span className="admin-badge">Admin</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="chat-area">
        <div className="messages-container">
          {messages.length > 0 ? (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`message ${msg.author_id === user?.id ? 'own' : ''}`}
              >
                <div className="message-header">
                  <span className="message-author">
                    {msg.author?.full_name || 'Unknown'}
                  </span>
                  <span className="message-time">
                    {new Date(msg.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="message-content">{msg.content}</p>
              </div>
            ))
          ) : (
            <div className="no-messages">
              <p>No messages yet. Start the conversation!</p>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSendMessage} className="message-form">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message..."
          />
          <button type="submit">Send</button>
        </form>
      </div>

      {showInvite && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Invite Member</h2>
            {inviteError && <div className="error-message">{inviteError}</div>}
            <form onSubmit={handleInvite}>
              <div className="form-group">
                <label>Email Address</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="Enter email to invite"
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowInvite(false)}>
                  Cancel
                </button>
                <button type="submit">Send Invite</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default GroupDetailPage;
