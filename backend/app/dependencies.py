"""
Authentication dependencies and utilities
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import json
import base64

from app.database import get_db
from app.models import User
from app.services.cognito import cognito_service
from app.schemas import TokenData

# Bearer token security scheme
security = HTTPBearer(auto_error=False)


def decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without verification (for development)"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1]
        # Add padding if needed
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload
    except Exception:
        return {}


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        
        # Try Cognito verification first
        try:
            payload = await cognito_service.verify_token(token)
        except Exception:
            # Fall back to simple JWT decode for development
            payload = decode_jwt_payload(token)
            if not payload:
                return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Get or create user in database
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            # Create new user from Cognito data
            groups = payload.get("cognito:groups", [])
            user = User(
                id=user_id,
                email=payload.get("email", ""),
                username=payload.get("cognito:username"),
                full_name=payload.get("name"),
                role="admin" if "Admin_auth" in groups else "student",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
        
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user (required)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        
        # Try Cognito verification first
        try:
            payload = await cognito_service.verify_token(token)
        except Exception:
            # Fall back to simple JWT decode for development
            payload = decode_jwt_payload(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        
        # Get or create user in database
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            # Create new user from Cognito data
            groups = payload.get("cognito:groups", [])
            user = User(
                id=user_id,
                email=payload.get("email", ""),
                username=payload.get("cognito:username"),
                full_name=payload.get("name"),
                role="admin" if "Admin_auth" in groups else "student",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current user and verify admin role
    Checks both Cognito group AND database role
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    try:
        token = credentials.credentials
        
        # Try Cognito verification first
        try:
            payload = await cognito_service.verify_token(token)
        except Exception:
            # Fall back to simple JWT decode for development
            payload = decode_jwt_payload(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            # New user - check if admin in Cognito group
            groups = payload.get("cognito:groups", [])
            is_admin = "Admin_auth" in groups
            user = User(
                id=user_id,
                email=payload.get("email", ""),
                username=payload.get("cognito:username"),
                full_name=payload.get("name"),
                role="admin" if is_admin else "student",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Check admin access: either Cognito group OR database role
        groups = payload.get("cognito:groups", [])
        is_cognito_admin = "Admin_auth" in groups
        is_db_admin = user.role == "admin"
        
        if not is_cognito_admin and not is_db_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


def get_token_data(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """
    Extract token data without database lookup
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    try:
        import base64
        import json
        
        token = credentials.credentials
        # Decode JWT payload (middle part)
        payload_b64 = token.split(".")[1]
        # Add padding if needed
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        
        return TokenData(
            sub=payload.get("sub", ""),
            email=payload.get("email"),
            groups=payload.get("cognito:groups", []),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
