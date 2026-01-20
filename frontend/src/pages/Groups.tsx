import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { groupService } from '../services/groupService';
import { Group, GroupInvitation } from '../types';
import './Groups.css';

const Groups: React.FC = () => {
  const [publicGroups, setPublicGroups] = useState<Group[]>([]);
  const [myGroups, setMyGroups] = useState<Group[]>([]);
  const [invitations, setInvitations] = useState<GroupInvitation[]>([]);
  const [activeTab, setActiveTab] = useState<'my' | 'discover'>('my');
  const [showCreate, setShowCreate] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [groupType, setGroupType] = useState('public');
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      const [publicRes, myRes, invites] = await Promise.all([
        groupService.listGroups(),
        groupService.listMyGroups(),
        groupService.getPendingInvitations(),
      ]);
      setPublicGroups(publicRes.groups);
      setMyGroups(myRes.groups);
      setInvitations(invites);
    } catch (err) {
      console.error('Failed to load groups:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      await groupService.createGroup(name, description, groupType);
      setName('');
      setDescription('');
      setGroupType('public');
      setShowCreate(false);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create group');
    }
  };

  const handleJoin = async (groupId: number) => {
    try {
      await groupService.joinGroup(groupId);
      await loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to join group');
    }
  };

  const handleAcceptInvite = async (invitationId: number) => {
    try {
      await groupService.acceptInvitation(invitationId);
      await loadData();
    } catch (err) {
      console.error('Failed to accept invitation:', err);
    }
  };

  const handleRejectInvite = async (invitationId: number) => {
    try {
      await groupService.rejectInvitation(invitationId);
      await loadData();
    } catch (err) {
      console.error('Failed to reject invitation:', err);
    }
  };

  const isJoined = (groupId: number) => {
    return myGroups.some(g => g.id === groupId);
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading groups...</p>
      </div>
    );
  }

  return (
    <div className="groups-page">
      <div className="page-header">
        <h1>Discussion Groups</h1>
        <button onClick={() => setShowCreate(true)} className="create-btn">
          + Create Group
        </button>
      </div>

      {invitations.length > 0 && (
        <div className="invitations-section">
          <h2>Pending Invitations</h2>
          <div className="invitations-list">
            {invitations.map((inv) => (
              <div key={inv.id} className="invitation-card">
                <div className="inv-info">
                  <strong>{inv.group_name}</strong>
                  <span>Invited by {inv.inviter_name}</span>
                </div>
                <div className="inv-actions">
                  <button onClick={() => handleAcceptInvite(inv.id)} className="accept-btn">
                    Accept
                  </button>
                  <button onClick={() => handleRejectInvite(inv.id)} className="reject-btn">
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {showCreate && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Create Group</h2>
            {error && <div className="error-message">{error}</div>}
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Group Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter group name"
                  required
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe your group"
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label>Group Type</label>
                <select value={groupType} onChange={(e) => setGroupType(e.target.value)}>
                  <option value="public">Public - Anyone can join</option>
                  <option value="private">Private - Invite only</option>
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreate(false)}>
                  Cancel
                </button>
                <button type="submit">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'my' ? 'active' : ''}`}
          onClick={() => setActiveTab('my')}
        >
          My Groups ({myGroups.length})
        </button>
        <button
          className={`tab ${activeTab === 'discover' ? 'active' : ''}`}
          onClick={() => setActiveTab('discover')}
        >
          Discover Groups
        </button>
      </div>

      <div className="groups-grid">
        {activeTab === 'my' ? (
          myGroups.length > 0 ? (
            myGroups.map((group) => (
              <Link to={`/groups/${group.id}`} key={group.id} className="group-card">
                <div className="group-icon">
                  {group.group_type === 'private' ? '🔒' : '🌐'}
                </div>
                <h3>{group.name}</h3>
                <p className="group-desc">{group.description || 'No description'}</p>
                <div className="group-meta">
                  <span>{group.member_count} members</span>
                  <span className={`type-badge ${group.group_type}`}>
                    {group.group_type}
                  </span>
                </div>
              </Link>
            ))
          ) : (
            <p className="empty-message">You haven't joined any groups yet.</p>
          )
        ) : (
          publicGroups.length > 0 ? (
            publicGroups.map((group) => (
              <div key={group.id} className="group-card discover">
                <div className="group-icon">🌐</div>
                <h3>{group.name}</h3>
                <p className="group-desc">{group.description || 'No description'}</p>
                <div className="group-meta">
                  <span>{group.member_count} members</span>
                </div>
                {isJoined(group.id) ? (
                  <Link to={`/groups/${group.id}`} className="view-btn">
                    View Group
                  </Link>
                ) : (
                  <button onClick={() => handleJoin(group.id)} className="join-btn">
                    Join Group
                  </button>
                )}
              </div>
            ))
          ) : (
            <p className="empty-message">No public groups available.</p>
          )
        )}
      </div>
    </div>
  );
};

export default Groups;
