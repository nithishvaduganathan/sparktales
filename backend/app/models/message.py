"""Message model for group discussions."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Message(Base):
    """Message model for group discussions."""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User", back_populates="messages")
    group = relationship("Group", back_populates="messages")
