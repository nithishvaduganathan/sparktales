"""AI Query schemas for request/response validation."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class AIQueryRequest(BaseModel):
    """Schema for AI query request."""
    query: str
    document_ids: Optional[List[int]] = None  # Specific documents to query


class AIQueryResponse(BaseModel):
    """Schema for AI query response."""
    id: int
    query: str
    response: str
    document_ids: Optional[str] = None
    processing_time: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AIQueryHistoryResponse(BaseModel):
    """Schema for AI query history response."""
    queries: List[AIQueryResponse]
    total: int
