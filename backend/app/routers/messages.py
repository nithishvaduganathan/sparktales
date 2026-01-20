"""Messages router for group discussions."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.group import Group, GroupMember, GroupType
from app.models.message import Message
from app.schemas.message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessageListResponse,
    AuthorInfo,
)
from app.utils.security import get_current_user, get_client_ip
from app.services.audit_service import log_action


router = APIRouter(prefix="/groups/{group_id}/messages", tags=["Messages"])


async def check_group_membership(
    group_id: int,
    user_id: int,
    db: AsyncSession,
) -> bool:
    """Check if user is a member of the group."""
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        )
    )
    return result.scalar_one_or_none() is not None


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    group_id: int,
    message_data: MessageCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new message in a group."""
    # Check if group exists
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    
    # Check membership
    if not await check_group_membership(group_id, current_user.id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be a group member to post messages",
        )
    
    # Create message
    message = Message(
        content=message_data.content,
        author_id=current_user.id,
        group_id=group_id,
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return MessageResponse(
        id=message.id,
        content=message.content,
        author_id=message.author_id,
        author=AuthorInfo(
            id=current_user.id,
            full_name=current_user.full_name,
            email=current_user.email,
        ),
        group_id=message.group_id,
        created_at=message.created_at,
        updated_at=message.updated_at,
    )


@router.get("/", response_model=MessageListResponse)
async def list_messages(
    group_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List messages in a group."""
    # Check if group exists
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    
    # For private groups, check membership
    if group.group_type == GroupType.PRIVATE.value:
        if not await check_group_membership(group_id, current_user.id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to private group",
            )
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.group_id == group_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()
    
    # Build response with author info
    message_responses = []
    for msg in messages:
        author_result = await db.execute(select(User).where(User.id == msg.author_id))
        author = author_result.scalar_one_or_none()
        
        message_responses.append(MessageResponse(
            id=msg.id,
            content=msg.content,
            author_id=msg.author_id,
            author=AuthorInfo(
                id=author.id,
                full_name=author.full_name,
                email=author.email,
            ) if author else None,
            group_id=msg.group_id,
            created_at=msg.created_at,
            updated_at=msg.updated_at,
        ))
    
    # Count total
    count_result = await db.execute(
        select(Message).where(Message.group_id == group_id)
    )
    total = len(count_result.scalars().all())
    
    return MessageListResponse(messages=message_responses, total=total)


@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(
    group_id: int,
    message_id: int,
    message_data: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a message (author only)."""
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.group_id == group_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    if message.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author can edit this message",
        )
    
    message.content = message_data.content
    await db.commit()
    await db.refresh(message)
    
    return MessageResponse(
        id=message.id,
        content=message.content,
        author_id=message.author_id,
        author=AuthorInfo(
            id=current_user.id,
            full_name=current_user.full_name,
            email=current_user.email,
        ),
        group_id=message.group_id,
        created_at=message.created_at,
        updated_at=message.updated_at,
    )


@router.delete("/{message_id}")
async def delete_message(
    group_id: int,
    message_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a message (author or group admin only)."""
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.group_id == group_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    
    # Check if user is author or group admin
    is_author = message.author_id == current_user.id
    
    admin_result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id,
            GroupMember.role == "admin"
        )
    )
    is_admin = admin_result.scalar_one_or_none() is not None
    
    if not is_author and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author or group admin can delete this message",
        )
    
    await db.delete(message)
    await db.commit()
    
    return {"message": "Message deleted successfully"}
