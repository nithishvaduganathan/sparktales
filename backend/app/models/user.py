"""User model definition."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    STUDENT = "student"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Base):
    """User model for authentication and profile."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.STUDENT.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="owner")
    owned_groups = relationship("Group", back_populates="owner")
    group_memberships = relationship("GroupMember", back_populates="user")
    messages = relationship("Message", back_populates="author")
    audit_logs = relationship("AuditLog", back_populates="user")
    ai_queries = relationship("AIQuery", back_populates="user")
