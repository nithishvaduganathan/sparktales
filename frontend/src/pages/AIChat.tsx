import React, { useState, useEffect, useRef } from 'react';
import { aiService } from '../services/aiService';
import { documentService } from '../services/documentService';
import { Document, AIQueryResponse } from '../types';
import './AIChat.css';

const AIChat: React.FC = () => {
  const [query, setQuery] = useState('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocs, setSelectedDocs] = useState<number[]>([]);
  const [history, setHistory] = useState<AIQueryResponse[]>([]);
  const [currentResponse, setCurrentResponse] = useState<AIQueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [docsRes, historyRes] = await Promise.all([
          documentService.listDocuments(0, 100),
          aiService.getQueryHistory(0, 10),
        ]);
        setDocuments(docsRes.documents.filter(d => d.is_processed));
        setHistory(historyRes.queries);
      } catch (err) {
        console.error('Failed to load data:', err);
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentResponse, history]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    if (documents.length === 0) {
      setError('Please upload and process documents first before asking questions.');
      return;
    }

    setIsLoading(true);
    setError('');
    setCurrentResponse(null);

    try {
      const response = await aiService.askQuestion(
        query,
        selectedDocs.length > 0 ? selectedDocs : undefined
      );
      setCurrentResponse(response);
      setHistory([response, ...history]);
      setQuery('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to get AI response');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleDocSelection = (docId: number) => {
    setSelectedDocs(prev =>
      prev.includes(docId)
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
    );
  };

  return (
    <div className="ai-chat-page">
      <div className="chat-sidebar">
        <h2>📚 Your Documents</h2>
        <p className="sidebar-desc">
          Select specific documents to search, or leave all unselected to search all documents.
        </p>
        
        {documents.length > 0 ? (
          <ul className="doc-selection-list">
            {documents.map((doc) => (
              <li key={doc.id}>
                <label className="doc-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedDocs.includes(doc.id)}
                    onChange={() => toggleDocSelection(doc.id)}
                  />
                  <span className="doc-title">{doc.title}</span>
                </label>
              </li>
            ))}
          </ul>
        ) : (
          <p className="no-docs-message">
            No processed documents available. Upload documents to start asking questions.
          </p>
        )}

        <div className="selection-actions">
          {selectedDocs.length > 0 && (
            <button onClick={() => setSelectedDocs([])} className="clear-btn">
              Clear Selection ({selectedDocs.length})
            </button>
          )}
        </div>
      </div>

      <div className="chat-main">
        <div className="chat-header">
          <h1>🤖 AI Assistant</h1>
          <p>Ask questions about your uploaded documents</p>
        </div>

        <div className="chat-messages">
          {error && <div className="error-message">{error}</div>}
          
          {currentResponse && (
            <div className="response-card">
              <div className="query-section">
                <span className="label">Your Question:</span>
                <p>{currentResponse.query}</p>
              </div>
              <div className="answer-section">
                <span className="label">AI Response:</span>
                <p>{currentResponse.response}</p>
                <div className="response-meta">
                  <span>Response time: {currentResponse.processing_time}ms</span>
                </div>
              </div>
            </div>
          )}

          {history.length > 0 && !currentResponse && (
            <div className="history-section">
              <h3>Recent Questions</h3>
              {history.slice(0, 5).map((item) => (
                <div key={item.id} className="history-item">
                  <p className="history-query">{item.query}</p>
                  <p className="history-response">{item.response.substring(0, 200)}...</p>
                  <span className="history-time">
                    {new Date(item.created_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}

          {!currentResponse && history.length === 0 && (
            <div className="welcome-message">
              <h2>👋 Welcome to AI Assistant</h2>
              <p>
                I can help you find information from your uploaded documents.
                Just type your question below!
              </p>
              <div className="example-questions">
                <p><strong>Example questions:</strong></p>
                <ul>
                  <li>"What are the main topics covered in the document?"</li>
                  <li>"Summarize the key points about..."</li>
                  <li>"Find information about..."</li>
                </ul>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="chat-form">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about your documents..."
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !query.trim()}>
            {isLoading ? 'Thinking...' : 'Ask'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AIChat;
