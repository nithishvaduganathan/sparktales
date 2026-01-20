"""Admin router for super admin operations."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List

from app.database import get_db
from app.models.user import User, UserRole
from app.models.document import Document
from app.models.group import Group
from app.models.audit import AuditLog
from app.models.ai_query import AIQuery
from app.schemas.user import UserResponse, UserStatusUpdate
from app.schemas.audit import AuditLogResponse, AuditLogListResponse, AdminDashboardStats
from app.schemas.group import GroupResponse, GroupListResponse
from app.utils.security import get_current_super_admin, get_client_ip
from app.services.audit_service import log_action


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=AdminDashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics for super admin."""
    # Total users
    users_result = await db.execute(select(User))
    total_users = len(users_result.scalars().all())
    
    # Active users
    active_result = await db.execute(select(User).where(User.is_active == True))
    active_users = len(active_result.scalars().all())
    
    # Total documents
    docs_result = await db.execute(select(Document))
    total_documents = len(docs_result.scalars().all())
    
    # Total groups
    groups_result = await db.execute(select(Group))
    total_groups = len(groups_result.scalars().all())
    
    # Total AI queries
    ai_result = await db.execute(select(AIQuery))
    total_ai_queries = len(ai_result.scalars().all())
    
    # Recent logins (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    logins_result = await db.execute(
        select(AuditLog).where(
            AuditLog.action == "user_login",
            AuditLog.created_at >= yesterday
        )
    )
    recent_logins = len(logins_result.scalars().all())
    
    # Failed logins (last 24 hours)
    failed_result = await db.execute(
        select(AuditLog).where(
            AuditLog.action == "login_failed",
            AuditLog.created_at >= yesterday
        )
    )
    failed_logins = len(failed_result.scalars().all())
    
    return AdminDashboardStats(
        total_users=total_users,
        active_users=active_users,
        total_documents=total_documents,
        total_groups=total_groups,
        total_ai_queries=total_ai_queries,
        recent_logins=recent_logins,
        failed_logins=failed_logins,
    )


@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users (super admin only)."""
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()
    return list(users)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific user's details."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@router.put("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.role == UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify super admin account",
        )
    
    user.is_active = status_update.is_active
    await db.commit()
    await db.refresh(user)
    
    # Log action
    action = "user_enabled" if status_update.is_active else "user_disabled"
    await log_action(
        db=db,
        action=action,
        user_id=current_user.id,
        resource_type="user",
        resource_id=user_id,
        details=f"User {user.email} {'enabled' if status_update.is_active else 'disabled'}",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    return user


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    skip: int = 0,
    limit: int = 50,
    action: str = None,
    user_id: int = None,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs with optional filtering."""
    query = select(AuditLog)
    
    if action:
        query = query.where(AuditLog.action == action)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    
    result = await db.execute(
        query.order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()
    
    # Count total
    count_query = select(AuditLog)
    if action:
        count_query = count_query.where(AuditLog.action == action)
    if user_id:
        count_query = count_query.where(AuditLog.user_id == user_id)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    return AuditLogListResponse(logs=list(logs), total=total)


@router.get("/groups", response_model=GroupListResponse)
async def list_all_groups(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all groups (super admin only)."""
    result = await db.execute(
        select(Group)
        .order_by(Group.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    groups = result.scalars().all()
    
    from app.models.group import GroupMember
    group_responses = []
    for group in groups:
        member_count_result = await db.execute(
            select(GroupMember).where(GroupMember.group_id == group.id)
        )
        member_count = len(member_count_result.scalars().all())
        
        group_responses.append(GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            group_type=group.group_type,
            is_active=group.is_active,
            owner_id=group.owner_id,
            created_at=group.created_at,
            member_count=member_count,
        ))
    
    return GroupListResponse(groups=group_responses, total=len(group_responses))


@router.delete("/groups/{group_id}")
async def admin_delete_group(
    group_id: int,
    request: Request,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete any group (super admin only)."""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    
    # Log deletion
    await log_action(
        db=db,
        action="admin_group_deleted",
        user_id=current_user.id,
        resource_type="group",
        resource_id=group_id,
        details=f"Admin deleted group: {group.name}",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    await db.delete(group)
    await db.commit()
    
    return {"message": "Group deleted successfully"}


@router.get("/documents", response_model=List[dict])
async def list_all_documents(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all documents (super admin only)."""
    result = await db.execute(
        select(Document)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()
    
    doc_responses = []
    for doc in documents:
        user_result = await db.execute(select(User).where(User.id == doc.owner_id))
        user = user_result.scalar_one_or_none()
        
        doc_responses.append({
            "id": doc.id,
            "title": doc.title,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "is_processed": doc.is_processed,
            "is_shared": doc.is_shared,
            "owner_id": doc.owner_id,
            "owner_email": user.email if user else None,
            "created_at": doc.created_at.isoformat(),
        })
    
    return doc_responses


@router.get("/ai-queries")
async def list_all_ai_queries(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all AI queries (super admin only)."""
    result = await db.execute(
        select(AIQuery)
        .order_by(AIQuery.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    queries = result.scalars().all()
    
    query_responses = []
    for q in queries:
        user_result = await db.execute(select(User).where(User.id == q.user_id))
        user = user_result.scalar_one_or_none()
        
        query_responses.append({
            "id": q.id,
            "user_id": q.user_id,
            "user_email": user.email if user else None,
            "query": q.query,
            "response": q.response[:200] + "..." if len(q.response) > 200 else q.response,
            "processing_time": q.processing_time,
            "created_at": q.created_at.isoformat(),
        })
    
    return query_responses
