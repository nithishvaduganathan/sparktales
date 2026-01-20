"""Groups router for discussion group management."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.group import Group, GroupMember, GroupInvitation, GroupType, MemberRole
from app.schemas.group import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupDetailResponse,
    GroupListResponse,
    GroupInvitationCreate,
    GroupInvitationResponse,
    MemberInfo,
)
from app.utils.security import get_current_user, get_client_ip
from app.services.audit_service import log_action


router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new discussion group."""
    # Validate group type
    if group_data.group_type not in [GroupType.PUBLIC.value, GroupType.PRIVATE.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group type. Must be 'public' or 'private'",
        )
    
    # Create group
    group = Group(
        name=group_data.name,
        description=group_data.description,
        group_type=group_data.group_type,
        owner_id=current_user.id,
    )
    
    db.add(group)
    await db.commit()
    await db.refresh(group)
    
    # Add creator as admin member
    member = GroupMember(
        user_id=current_user.id,
        group_id=group.id,
        role=MemberRole.ADMIN.value,
    )
    db.add(member)
    await db.commit()
    
    # Log group creation
    await log_action(
        db=db,
        action="group_created",
        user_id=current_user.id,
        resource_type="group",
        resource_id=group.id,
        details=f"Created group: {group.name} ({group.group_type})",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        group_type=group.group_type,
        is_active=group.is_active,
        owner_id=group.owner_id,
        created_at=group.created_at,
        member_count=1,
    )


@router.get("/", response_model=GroupListResponse)
async def list_groups(
    skip: int = 0,
    limit: int = 20,
    include_private: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List available groups."""
    if include_private:
        # Include private groups where user is a member
        result = await db.execute(
            select(Group)
            .where(Group.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(Group.created_at.desc())
        )
    else:
        # Only public groups
        result = await db.execute(
            select(Group)
            .where(Group.is_active == True, Group.group_type == GroupType.PUBLIC.value)
            .offset(skip)
            .limit(limit)
            .order_by(Group.created_at.desc())
        )
    
    groups = result.scalars().all()
    
    # Get member counts
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


@router.get("/my-groups", response_model=GroupListResponse)
async def list_my_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List groups where user is a member."""
    # Get user's memberships
    result = await db.execute(
        select(GroupMember).where(GroupMember.user_id == current_user.id)
    )
    memberships = result.scalars().all()
    group_ids = [m.group_id for m in memberships]
    
    if not group_ids:
        return GroupListResponse(groups=[], total=0)
    
    # Get groups
    result = await db.execute(
        select(Group).where(Group.id.in_(group_ids))
    )
    groups = result.scalars().all()
    
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


@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get group details with members."""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    
    # Check access for private groups
    if group.group_type == GroupType.PRIVATE.value:
        member_result = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == current_user.id
            )
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to private group",
            )
    
    # Get members
    members_result = await db.execute(
        select(GroupMember).where(GroupMember.group_id == group_id)
    )
    members = members_result.scalars().all()
    
    member_infos = []
    for member in members:
        user_result = await db.execute(select(User).where(User.id == member.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            member_infos.append(MemberInfo(
                id=member.id,
                user_id=user.id,
                full_name=user.full_name,
                email=user.email,
                role=member.role,
                joined_at=member.joined_at,
            ))
    
    return GroupDetailResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        group_type=group.group_type,
        is_active=group.is_active,
        owner_id=group.owner_id,
        created_at=group.created_at,
        member_count=len(member_infos),
        members=member_infos,
    )


@router.post("/{group_id}/join")
async def join_group(
    group_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a public group."""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    
    if group.group_type == GroupType.PRIVATE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot join private group directly. Requires invitation.",
        )
    
    # Check if already a member
    member_result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        )
    )
    if member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this group",
        )
    
    # Add as member
    member = GroupMember(
        user_id=current_user.id,
        group_id=group_id,
        role=MemberRole.MEMBER.value,
    )
    db.add(member)
    await db.commit()
    
    # Log join
    await log_action(
        db=db,
        action="group_joined",
        user_id=current_user.id,
        resource_type="group",
        resource_id=group_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    return {"message": f"Successfully joined group: {group.name}"}


@router.post("/{group_id}/leave")
async def leave_group(
    group_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a group."""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    
    if group.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group owner cannot leave. Transfer ownership or delete the group.",
        )
    
    member_result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        )
    )
    member = member_result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a member of this group",
        )
    
    await db.delete(member)
    await db.commit()
    
    # Log leave
    await log_action(
        db=db,
        action="group_left",
        user_id=current_user.id,
        resource_type="group",
        resource_id=group_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    return {"message": f"Left group: {group.name}"}


@router.post("/{group_id}/invite", response_model=GroupInvitationResponse)
async def invite_to_group(
    group_id: int,
    invitation: GroupInvitationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invite a user to a private group (admin only)."""
    # Get group
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    
    # Check if user is admin
    member_result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id,
            GroupMember.role == MemberRole.ADMIN.value
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can send invitations",
        )
    
    # Find invitee
    invitee_result = await db.execute(
        select(User).where(User.email == invitation.invitee_email)
    )
    invitee = invitee_result.scalar_one_or_none()
    
    if not invitee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Check if already a member
    existing_member = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == invitee.id
        )
    )
    if existing_member.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member",
        )
    
    # Create invitation
    group_invitation = GroupInvitation(
        group_id=group_id,
        inviter_id=current_user.id,
        invitee_id=invitee.id,
    )
    db.add(group_invitation)
    await db.commit()
    await db.refresh(group_invitation)
    
    return GroupInvitationResponse(
        id=group_invitation.id,
        group_id=group_id,
        group_name=group.name,
        inviter_name=current_user.full_name,
        status=group_invitation.status,
        created_at=group_invitation.created_at,
    )


@router.get("/invitations/pending", response_model=List[GroupInvitationResponse])
async def get_pending_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pending invitations for current user."""
    result = await db.execute(
        select(GroupInvitation).where(
            GroupInvitation.invitee_id == current_user.id,
            GroupInvitation.status == "pending"
        )
    )
    invitations = result.scalars().all()
    
    responses = []
    for inv in invitations:
        group_result = await db.execute(select(Group).where(Group.id == inv.group_id))
        group = group_result.scalar_one_or_none()
        
        inviter_result = await db.execute(select(User).where(User.id == inv.inviter_id))
        inviter = inviter_result.scalar_one_or_none()
        
        if group and inviter:
            responses.append(GroupInvitationResponse(
                id=inv.id,
                group_id=inv.group_id,
                group_name=group.name,
                inviter_name=inviter.full_name,
                status=inv.status,
                created_at=inv.created_at,
            ))
    
    return responses


@router.post("/invitations/{invitation_id}/accept")
async def accept_invitation(
    invitation_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept a group invitation."""
    result = await db.execute(
        select(GroupInvitation).where(
            GroupInvitation.id == invitation_id,
            GroupInvitation.invitee_id == current_user.id
        )
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    
    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already processed",
        )
    
    # Update invitation
    from datetime import datetime
    invitation.status = "accepted"
    invitation.responded_at = datetime.utcnow()
    
    # Add as member
    member = GroupMember(
        user_id=current_user.id,
        group_id=invitation.group_id,
        role=MemberRole.MEMBER.value,
    )
    db.add(member)
    await db.commit()
    
    return {"message": "Invitation accepted"}


@router.post("/invitations/{invitation_id}/reject")
async def reject_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a group invitation."""
    result = await db.execute(
        select(GroupInvitation).where(
            GroupInvitation.id == invitation_id,
            GroupInvitation.invitee_id == current_user.id
        )
    )
    invitation = result.scalar_one_or_none()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    
    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already processed",
        )
    
    from datetime import datetime
    invitation.status = "rejected"
    invitation.responded_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Invitation rejected"}


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a group (owner only)."""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    
    if group.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can delete the group",
        )
    
    # Log deletion
    await log_action(
        db=db,
        action="group_deleted",
        user_id=current_user.id,
        resource_type="group",
        resource_id=group_id,
        details=f"Deleted group: {group.name}",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    await db.delete(group)
    await db.commit()
    
    return {"message": "Group deleted successfully"}
