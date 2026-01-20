"""AI Router for RAG-powered Q&A."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.ai_query import AIQuery
from app.schemas.ai_query import AIQueryRequest, AIQueryResponse, AIQueryHistoryResponse
from app.utils.security import get_current_user, get_client_ip
from app.services.audit_service import log_action
from app.services.rag_service import rag_service


router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/query", response_model=AIQueryResponse)
async def ask_question(
    query_data: AIQueryRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ask a question to the AI RAG system.
    The AI will search through the user's documents and generate a context-aware response.
    """
    # Get user's documents
    doc_ids = query_data.document_ids
    
    if not doc_ids:
        # Use all user's documents
        result = await db.execute(
            select(Document).where(
                Document.owner_id == current_user.id,
                Document.is_processed == True
            )
        )
        documents = result.scalars().all()
        doc_ids = [doc.id for doc in documents]
    else:
        # Validate document access
        result = await db.execute(
            select(Document).where(
                Document.id.in_(doc_ids),
                (Document.owner_id == current_user.id) | (Document.is_shared == True)
            )
        )
        documents = result.scalars().all()
        accessible_ids = {doc.id for doc in documents}
        
        for doc_id in doc_ids:
            if doc_id not in accessible_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to document {doc_id}",
                )
    
    if not doc_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents available. Please upload documents first.",
        )
    
    # Load documents into RAG service if not already loaded
    for doc in documents:
        if doc.content_text:
            rag_service.add_document(doc.id, doc.content_text)
    
    # Generate response
    response_text, processing_time = rag_service.generate_response(
        query_data.query,
        doc_ids
    )
    
    # Save query to database
    ai_query = AIQuery(
        user_id=current_user.id,
        query=query_data.query,
        response=response_text,
        document_ids=",".join(map(str, doc_ids)),
        processing_time=processing_time,
    )
    
    db.add(ai_query)
    await db.commit()
    await db.refresh(ai_query)
    
    # Log AI query
    await log_action(
        db=db,
        action="ai_query",
        user_id=current_user.id,
        resource_type="ai_query",
        resource_id=ai_query.id,
        details=f"Query: {query_data.query[:100]}...",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    return AIQueryResponse(
        id=ai_query.id,
        query=ai_query.query,
        response=ai_query.response,
        document_ids=ai_query.document_ids,
        processing_time=ai_query.processing_time,
        created_at=ai_query.created_at,
    )


@router.get("/history", response_model=AIQueryHistoryResponse)
async def get_query_history(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's AI query history."""
    result = await db.execute(
        select(AIQuery)
        .where(AIQuery.user_id == current_user.id)
        .order_by(AIQuery.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    queries = result.scalars().all()
    
    count_result = await db.execute(
        select(AIQuery).where(AIQuery.user_id == current_user.id)
    )
    total = len(count_result.scalars().all())
    
    return AIQueryHistoryResponse(
        queries=[
            AIQueryResponse(
                id=q.id,
                query=q.query,
                response=q.response,
                document_ids=q.document_ids,
                processing_time=q.processing_time,
                created_at=q.created_at,
            )
            for q in queries
        ],
        total=total,
    )


@router.get("/query/{query_id}", response_model=AIQueryResponse)
async def get_query(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific AI query."""
    result = await db.execute(
        select(AIQuery).where(
            AIQuery.id == query_id,
            AIQuery.user_id == current_user.id
        )
    )
    query = result.scalar_one_or_none()
    
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found",
        )
    
    return AIQueryResponse(
        id=query.id,
        query=query.query,
        response=query.response,
        document_ids=query.document_ids,
        processing_time=query.processing_time,
        created_at=query.created_at,
    )
