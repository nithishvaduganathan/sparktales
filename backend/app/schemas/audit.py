"""Audit log schemas for request/response validation."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: int
    user_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    success: int
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema for audit log list response."""
    logs: List[AuditLogResponse]
    total: int


class AdminDashboardStats(BaseModel):
    """Schema for admin dashboard statistics."""
    total_users: int
    active_users: int
    total_documents: int
    total_groups: int
    total_ai_queries: int
    recent_logins: int
    failed_logins: int
