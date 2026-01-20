"""Document schemas for request/response validation."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentBase(BaseModel):
    """Base document schema."""
    title: str


class DocumentCreate(DocumentBase):
    """Schema for document creation."""
    pass


class DocumentUpdate(BaseModel):
    """Schema for document update."""
    title: Optional[str] = None
    is_shared: Optional[bool] = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: int
    filename: str
    file_type: str
    file_size: int
    is_processed: bool
    is_shared: bool
    owner_id: int
    group_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for document list response."""
    documents: list[DocumentResponse]
    total: int
