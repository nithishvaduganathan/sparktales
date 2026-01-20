"""Document router for file upload and management."""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentUpdate
from app.utils.security import get_current_user, get_client_ip
from app.services.audit_service import log_action
from app.services.document_service import extract_text
from app.services.rag_service import rag_service
from app.config import settings


router = APIRouter(prefix="/documents", tags=["Documents"])


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return os.path.splitext(filename)[1].lower()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    title: str = Form(...),
    file: UploadFile = File(...),
    group_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new document."""
    # Validate file extension
    file_extension = get_file_extension(file.filename)
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}",
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed ({settings.MAX_FILE_SIZE / 1024 / 1024}MB)",
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Extract text content
    content_text = extract_text(file_path, file_extension)
    
    # Create document record
    document = Document(
        title=title,
        filename=file.filename,
        file_path=file_path,
        file_type=file_extension,
        file_size=file_size,
        content_text=content_text,
        is_processed=bool(content_text),
        owner_id=current_user.id,
        group_id=group_id,
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Add to RAG service
    if content_text:
        rag_service.add_document(document.id, content_text)
    
    # Log upload
    await log_action(
        db=db,
        action="document_uploaded",
        user_id=current_user.id,
        resource_type="document",
        resource_id=document.id,
        details=f"Uploaded file: {file.filename}",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    return document


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's documents."""
    # Get user's own documents
    result = await db.execute(
        select(Document)
        .where(Document.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    
    # Count total
    count_result = await db.execute(
        select(Document).where(Document.owner_id == current_user.id)
    )
    total = len(count_result.scalars().all())
    
    return DocumentListResponse(documents=list(documents), total=total)


@router.get("/shared", response_model=DocumentListResponse)
async def list_shared_documents(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List shared documents."""
    result = await db.execute(
        select(Document)
        .where(Document.is_shared == True)
        .offset(skip)
        .limit(limit)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    
    count_result = await db.execute(
        select(Document).where(Document.is_shared == True)
    )
    total = len(count_result.scalars().all())
    
    return DocumentListResponse(documents=list(documents), total=total)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Check access (owner or shared)
    if document.owner_id != current_user.id and not document.is_shared:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a document."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Update fields
    if document_update.title is not None:
        document.title = document_update.title
    if document_update.is_shared is not None:
        document.is_shared = document_update.is_shared
    
    await db.commit()
    await db.refresh(document)
    
    # Log update
    await log_action(
        db=db,
        action="document_updated",
        user_id=current_user.id,
        resource_type="document",
        resource_id=document.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    if document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Remove file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Remove from RAG service
    rag_service.remove_document(document.id)
    
    # Log deletion
    await log_action(
        db=db,
        action="document_deleted",
        user_id=current_user.id,
        resource_type="document",
        resource_id=document.id,
        details=f"Deleted file: {document.filename}",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    await db.delete(document)
    await db.commit()
    
    return {"message": "Document deleted successfully"}
