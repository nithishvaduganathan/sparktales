"""Message schemas for request/response validation."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class MessageBase(BaseModel):
    """Base message schema."""
    content: str


class MessageCreate(MessageBase):
    """Schema for message creation."""
    pass


class MessageUpdate(BaseModel):
    """Schema for message update."""
    content: str


class AuthorInfo(BaseModel):
    """Schema for message author info."""
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: int
    author_id: int
    author: Optional[AuthorInfo] = None
    group_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Schema for message list response."""
    messages: List[MessageResponse]
    total: int
