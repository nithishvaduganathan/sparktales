"""Audit log model for tracking user activities."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class AuditLog(Base):
    """Audit log model for tracking all user activities."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    success = Column(Integer, default=1)  # 1 for success, 0 for failure
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
