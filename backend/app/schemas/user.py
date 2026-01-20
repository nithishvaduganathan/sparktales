"""User schemas for request/response validation."""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload schema."""
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


class UserStatusUpdate(BaseModel):
    """Schema for admin to update user status."""
    is_active: bool
