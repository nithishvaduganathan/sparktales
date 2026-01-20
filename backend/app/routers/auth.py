"""Authentication router for user registration and login."""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_client_ip,
)
from app.services.audit_service import log_action
from app.config import settings


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Determine role (super admin for specific email)
    role = UserRole.STUDENT.value
    if user_data.email == settings.SUPER_ADMIN_EMAIL:
        role = UserRole.SUPER_ADMIN.value
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=role,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Log registration
    await log_action(
        db=db,
        action="user_registered",
        user_id=new_user.id,
        resource_type="user",
        resource_id=new_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return access token."""
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        # Log failed login attempt
        await log_action(
            db=db,
            action="login_failed",
            details=f"Failed login attempt for email: {user_data.email}",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            success=False,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    # Log successful login
    await log_action(
        db=db,
        action="user_login",
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout user (for audit logging purposes)."""
    await log_action(
        db=db,
        action="user_logout",
        user_id=current_user.id,
        resource_type="user",
        resource_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return {"message": "Logged out successfully"}
