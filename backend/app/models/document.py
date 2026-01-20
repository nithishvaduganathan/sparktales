"""Document model definition."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Document(Base):
    """Document model for file uploads."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_text = Column(Text, nullable=True)  # Extracted text content
    is_processed = Column(Boolean, default=False)
    is_shared = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="documents")
    group = relationship("Group", back_populates="documents")
