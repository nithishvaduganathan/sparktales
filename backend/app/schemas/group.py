"""Group schemas for request/response validation."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class GroupBase(BaseModel):
    """Base group schema."""
    name: str
    description: Optional[str] = None


class GroupCreate(GroupBase):
    """Schema for group creation."""
    group_type: str = "public"  # public or private


class GroupUpdate(BaseModel):
    """Schema for group update."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class MemberInfo(BaseModel):
    """Schema for group member info."""
    id: int
    user_id: int
    full_name: str
    email: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class GroupResponse(GroupBase):
    """Schema for group response."""
    id: int
    group_type: str
    is_active: bool
    owner_id: int
    created_at: datetime
    member_count: Optional[int] = 0

    class Config:
        from_attributes = True


class GroupDetailResponse(GroupResponse):
    """Schema for detailed group response with members."""
    members: List[MemberInfo] = []


class GroupListResponse(BaseModel):
    """Schema for group list response."""
    groups: List[GroupResponse]
    total: int


class GroupInvitationCreate(BaseModel):
    """Schema for creating group invitation."""
    invitee_email: str


class GroupInvitationResponse(BaseModel):
    """Schema for group invitation response."""
    id: int
    group_id: int
    group_name: str
    inviter_name: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
