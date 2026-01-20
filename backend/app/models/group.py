"""Group and GroupMember models for discussion groups."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class GroupType(str, enum.Enum):
    """Group type enumeration."""
    PUBLIC = "public"
    PRIVATE = "private"


class MemberRole(str, enum.Enum):
    """Group member role enumeration."""
    MEMBER = "member"
    ADMIN = "admin"


class Group(Base):
    """Group model for discussion groups."""
    
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    group_type = Column(String(50), default=GroupType.PUBLIC.value)
    is_active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="owned_groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="group", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="group")


class GroupMember(Base):
    """Group member model for tracking group memberships."""
    
    __tablename__ = "group_members"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    role = Column(String(50), default=MemberRole.MEMBER.value)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="group_memberships")
    group = relationship("Group", back_populates="members")


class GroupInvitation(Base):
    """Group invitation model for private group invites."""
    
    __tablename__ = "group_invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invitee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)
