"""AI Query model for tracking RAG usage."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class AIQuery(Base):
    """AI Query model for tracking RAG system usage."""
    
    __tablename__ = "ai_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    document_ids = Column(String(500), nullable=True)  # Comma-separated document IDs used
    processing_time = Column(Integer, nullable=True)  # In milliseconds
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="ai_queries")
