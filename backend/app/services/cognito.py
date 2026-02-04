"""
AWS Cognito authentication service
"""
import boto3
import httpx
from jose import jwt, JWTError
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.config import get_settings

settings = get_settings()


class CognitoService:
    """Service for AWS Cognito authentication"""
    
    def __init__(self):
        self.client = boto3.client(
            'cognito-idp',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.user_pool_id = settings.cognito_user_pool_id
        self.client_id = settings.cognito_client_id
        self.client_secret = settings.cognito_client_secret
        self.domain = settings.cognito_domain
        self.region = settings.aws_region
        
        # Cache for JWKS (JSON Web Key Set)
        self._jwks: Optional[Dict] = None
    
    @property
    def jwks_url(self) -> str:
        """Get the JWKS URL for the user pool"""
        return f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
    
    @property
    def issuer(self) -> str:
        """Get the token issuer URL"""
        return f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
    
    async def get_jwks(self) -> Dict:
        """Fetch and cache JWKS from Cognito"""
        if self._jwks is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                self._jwks = response.json()
        return self._jwks
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a Cognito JWT token
        
        Args:
            token: The JWT token to verify
            
        Returns:
            The decoded token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Get JWKS
            jwks = await self.get_jwks()
            
            # Get the key ID from the token header
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            # Find the matching key
            rsa_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    rsa_key = key
                    break
            
            if not rsa_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token key not found"
                )
            
            # Verify and decode the token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer,
            )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}"
            )
    
    def get_user_groups(self, payload: Dict) -> list:
        """Extract user groups from token payload"""
        return payload.get("cognito:groups", [])
    
    def is_admin(self, payload: Dict) -> bool:
        """Check if user is an admin"""
        groups = self.get_user_groups(payload)
        return "Admin_auth" in groups
    
    def is_student(self, payload: Dict) -> bool:
        """Check if user is a student"""
        groups = self.get_user_groups(payload)
        return "Students_auth" in groups
    
    def get_login_url(self, redirect_uri: str) -> str:
        """Generate Cognito hosted UI login URL"""
        return (
            f"https://{self.domain}/login?"
            f"client_id={self.client_id}&"
            f"response_type=token&"
            f"scope=email+openid+profile&"
            f"redirect_uri={redirect_uri}"
        )
    
    def get_logout_url(self, redirect_uri: str) -> str:
        """Generate Cognito hosted UI logout URL"""
        return (
            f"https://{self.domain}/logout?"
            f"client_id={self.client_id}&"
            f"logout_uri={redirect_uri}"
        )
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get user info from Cognito using access token"""
        try:
            response = self.client.get_user(AccessToken=access_token)
            
            user_attributes = {}
            for attr in response.get("UserAttributes", []):
                user_attributes[attr["Name"]] = attr["Value"]
            
            return {
                "username": response.get("Username"),
                "sub": user_attributes.get("sub"),
                "email": user_attributes.get("email"),
                "email_verified": user_attributes.get("email_verified") == "true",
                "name": user_attributes.get("name"),
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to get user info: {str(e)}"
            )
    
    def admin_get_user(self, username: str) -> Dict:
        """Admin operation to get user details"""
        try:
            response = self.client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=username
            )
            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {str(e)}"
            )


# Singleton instance
cognito_service = CognitoService()
