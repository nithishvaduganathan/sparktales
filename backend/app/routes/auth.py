"""
Authentication routes for AWS Cognito
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserResponse, UserUpdate
from app.services.cognito import cognito_service
from app.dependencies import get_current_user, get_token_data
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.get("/login")
async def login():
    """
    Redirect to Cognito hosted UI for login
    """
    redirect_uri = f"{settings.frontend_url}/callback"
    login_url = cognito_service.get_login_url(redirect_uri)
    return RedirectResponse(url=login_url)


@router.get("/logout")
async def logout():
    """
    Redirect to Cognito hosted UI for logout
    """
    redirect_uri = settings.frontend_url
    logout_url = cognito_service.get_logout_url(redirect_uri)
    return RedirectResponse(url=logout_url)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user's information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update current user's profile
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for key, value in update_dict.items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/make-admin", response_model=UserResponse)
async def make_current_user_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Promote current user to admin role (Development only)
    This allows any authenticated user to become admin
    """
    current_user.role = "admin"
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/verify")
async def verify_token(
    token_data = Depends(get_token_data),
):
    """
    Verify a JWT token and return user info
    """
    return {
        "valid": True,
        "sub": token_data.sub,
        "email": token_data.email,
        "groups": token_data.groups,
        "is_admin": "Admin_auth" in token_data.groups,
        "is_student": "Students_auth" in token_data.groups,
    }


@router.get("/cognito/config")
async def get_cognito_config():
    """
    Get Cognito configuration for frontend
    (Only safe-to-expose values)
    """
    return {
        "region": settings.aws_region,
        "userPoolId": settings.cognito_user_pool_id,
        "clientId": settings.cognito_client_id,
        "domain": settings.cognito_domain,
    }
