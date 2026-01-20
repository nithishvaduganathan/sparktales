import React, { useState, useEffect } from 'react';
import { documentService } from '../services/documentService';
import { Document } from '../types';
import './Documents.css';

const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [sharedDocuments, setSharedDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'my' | 'shared'>('my');
  const [showUpload, setShowUpload] = useState(false);
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const loadDocuments = async () => {
    try {
      const [myDocs, sharedDocs] = await Promise.all([
        documentService.listDocuments(),
        documentService.listSharedDocuments(),
      ]);
      setDocuments(myDocs.documents);
      setSharedDocuments(sharedDocs.documents);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');

    try {
      await documentService.uploadDocument(title, file);
      setTitle('');
      setFile(null);
      setShowUpload(false);
      await loadDocuments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleShare = async (doc: Document) => {
    try {
      await documentService.updateDocument(doc.id, { is_shared: !doc.is_shared });
      await loadDocuments();
    } catch (err) {
      console.error('Failed to update document:', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await documentService.deleteDocument(id);
        await loadDocuments();
      } catch (err) {
        console.error('Failed to delete document:', err);
      }
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading documents...</p>
      </div>
    );
  }

  return (
    <div className="documents-page">
      <div className="page-header">
        <h1>Documents</h1>
        <button onClick={() => setShowUpload(true)} className="upload-btn">
          + Upload Document
        </button>
      </div>

      {showUpload && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Upload Document</h2>
            {error && <div className="error-message">{error}</div>}
            <form onSubmit={handleUpload}>
              <div className="form-group">
                <label>Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Document title"
                  required
                />
              </div>
              <div className="form-group">
                <label>File (PDF, TXT, DOCX)</label>
                <input
                  type="file"
                  accept=".pdf,.txt,.docx"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowUpload(false)}>
                  Cancel
                </button>
                <button type="submit" disabled={uploading}>
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
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
          My Documents ({documents.length})
        </button>
        <button
          className={`tab ${activeTab === 'shared' ? 'active' : ''}`}
          onClick={() => setActiveTab('shared')}
        >
          Shared Documents ({sharedDocuments.length})
        </button>
      </div>

      <div className="documents-grid">
        {(activeTab === 'my' ? documents : sharedDocuments).map((doc) => (
          <div key={doc.id} className="document-card">
            <div className="doc-header">
              <span className="doc-icon">
                {doc.file_type === '.pdf' ? '📕' : doc.file_type === '.txt' ? '📄' : '📝'}
              </span>
              <div className="doc-status">
                {doc.is_processed && <span className="badge processed">Processed</span>}
                {doc.is_shared && <span className="badge shared">Shared</span>}
              </div>
            </div>
            <h3>{doc.title}</h3>
            <p className="doc-filename">{doc.filename}</p>
            <p className="doc-meta">
              {formatFileSize(doc.file_size)} • {new Date(doc.created_at).toLocaleDateString()}
            </p>
            {activeTab === 'my' && (
              <div className="doc-actions">
                <button onClick={() => handleShare(doc)} className="share-btn">
                  {doc.is_shared ? 'Unshare' : 'Share'}
                </button>
                <button onClick={() => handleDelete(doc.id)} className="delete-btn">
                  Delete
                </button>
              </div>
            )}
          </div>
        ))}
        {(activeTab === 'my' ? documents : sharedDocuments).length === 0 && (
          <p className="empty-message">
            {activeTab === 'my' 
              ? "You haven't uploaded any documents yet." 
              : "No shared documents available."}
          </p>
        )}
      </div>
    </div>
  );
};

export default Documents;
