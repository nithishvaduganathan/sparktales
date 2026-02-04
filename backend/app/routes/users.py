"""
Admin routes for Cognito user management
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import boto3
import csv
import io

from app.models import User
from app.dependencies import get_current_admin
from app.config import get_settings

router = APIRouter(prefix="/admin/users", tags=["Admin - User Management"])
settings = get_settings()

# Initialize Cognito client
cognito_client = boto3.client(
    'cognito-idp',
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
)


# ============ Schemas ============

class CreateUserRequest(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    temporary_password: Optional[str] = None
    group: str = "Students_auth"  # Default to student group
    send_email: bool = True


class CreateUserResponse(BaseModel):
    success: bool
    email: str
    username: str
    message: str


class BulkUploadResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: List[dict]


# ============ Helper Functions ============

def generate_temp_password():
    """Generate a temporary password that meets Cognito requirements"""
    import secrets
    import string
    # At least 8 chars, uppercase, lowercase, number, special char
    password = (
        secrets.choice(string.ascii_uppercase) +
        secrets.choice(string.ascii_lowercase) +
        secrets.choice(string.digits) +
        secrets.choice("!@#$%^&*") +
        ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    )
    return password


def create_cognito_user(
    email: str,
    username: Optional[str] = None,
    full_name: Optional[str] = None,
    temporary_password: Optional[str] = None,
    group: str = "Students_auth",
    send_email: bool = True
) -> dict:
    """
    Create a user in Cognito and add to specified group
    """
    # Use email as username if not provided
    if not username:
        username = email.split('@')[0]
    
    # Generate password if not provided
    if not temporary_password:
        temporary_password = generate_temp_password()
    
    try:
        # Create user in Cognito
        user_attributes = [
            {'Name': 'email', 'Value': email},
            {'Name': 'email_verified', 'Value': 'true'},
        ]
        
        if full_name:
            user_attributes.append({'Name': 'name', 'Value': full_name})
        
        # Determine message action
        message_action = 'SUPPRESS' if not send_email else None
        
        create_params = {
            'UserPoolId': settings.cognito_user_pool_id,
            'Username': username,
            'UserAttributes': user_attributes,
            'TemporaryPassword': temporary_password,
            'ForceAliasCreation': False,
        }
        
        if message_action:
            create_params['MessageAction'] = message_action
        
        response = cognito_client.admin_create_user(**create_params)
        
        # Add user to group
        try:
            cognito_client.admin_add_user_to_group(
                UserPoolId=settings.cognito_user_pool_id,
                Username=username,
                GroupName=group
            )
        except cognito_client.exceptions.ResourceNotFoundException:
            # Group doesn't exist, try to create it
            try:
                cognito_client.create_group(
                    UserPoolId=settings.cognito_user_pool_id,
                    GroupName=group,
                    Description=f"{group} group"
                )
                # Try adding to group again
                cognito_client.admin_add_user_to_group(
                    UserPoolId=settings.cognito_user_pool_id,
                    Username=username,
                    GroupName=group
                )
            except Exception as e:
                print(f"Warning: Could not add user to group: {e}")
        
        return {
            'success': True,
            'email': email,
            'username': username,
            'message': f"User created successfully. {'Email sent with temporary password.' if send_email else f'Temporary password: {temporary_password}'}"
        }
        
    except cognito_client.exceptions.UsernameExistsException:
        return {
            'success': False,
            'email': email,
            'username': username,
            'message': 'User with this email/username already exists'
        }
    except cognito_client.exceptions.InvalidPasswordException as e:
        return {
            'success': False,
            'email': email,
            'username': username,
            'message': f'Invalid password: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'email': email,
            'username': username or email,
            'message': f'Error creating user: {str(e)}'
        }


# ============ API Endpoints ============

@router.post("/create", response_model=CreateUserResponse)
async def create_single_user(
    user_data: CreateUserRequest,
    current_admin: User = Depends(get_current_admin),
):
    """
    Create a single user in Cognito (Admin only)
    
    - **email**: User's email address (required)
    - **username**: Username (optional, defaults to email prefix)
    - **full_name**: User's full name (optional)
    - **temporary_password**: Temporary password (optional, auto-generated if not provided)
    - **group**: Cognito group to add user to (default: Students_auth)
    - **send_email**: Whether to send welcome email with password (default: true)
    """
    result = create_cognito_user(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        temporary_password=user_data.temporary_password,
        group=user_data.group,
        send_email=user_data.send_email
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.post("/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_users(
    file: UploadFile = File(...),
    group: str = Form("Students_auth"),
    send_email: bool = Form(True),
    current_admin: User = Depends(get_current_admin),
):
    """
    Bulk upload users from CSV file (Admin only)
    
    CSV file format:
    ```
    email,username,full_name,password
    john@example.com,john,John Doe,TempPass123!
    jane@example.com,jane,Jane Smith,
    ```
    
    - **email**: Required
    - **username**: Optional (defaults to email prefix)
    - **full_name**: Optional
    - **password**: Optional (auto-generated if empty)
    
    Parameters:
    - **file**: CSV file to upload
    - **group**: Cognito group to add users to (default: Students_auth)
    - **send_email**: Whether to send welcome emails (default: true)
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    # Read and parse CSV
    try:
        content = await file.read()
        decoded = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        
        results = []
        successful = 0
        failed = 0
        
        for row in reader:
            email = row.get('email', '').strip()
            
            if not email:
                results.append({
                    'success': False,
                    'email': 'N/A',
                    'message': 'Missing email in row'
                })
                failed += 1
                continue
            
            result = create_cognito_user(
                email=email,
                username=row.get('username', '').strip() or None,
                full_name=row.get('full_name', '').strip() or None,
                temporary_password=row.get('password', '').strip() or None,
                group=group,
                send_email=send_email
            )
            
            results.append(result)
            if result['success']:
                successful += 1
            else:
                failed += 1
        
        return BulkUploadResponse(
            total=len(results),
            successful=successful,
            failed=failed,
            results=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")


@router.get("/list")
async def list_cognito_users(
    limit: int = 60,
    pagination_token: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
):
    """
    List all users in Cognito (Admin only)
    """
    try:
        params = {
            'UserPoolId': settings.cognito_user_pool_id,
            'Limit': limit,
        }
        
        if pagination_token:
            params['PaginationToken'] = pagination_token
        
        response = cognito_client.list_users(**params)
        
        users = []
        for user in response.get('Users', []):
            user_data = {
                'username': user['Username'],
                'status': user['UserStatus'],
                'enabled': user['Enabled'],
                'created': user['UserCreateDate'].isoformat(),
                'attributes': {}
            }
            
            for attr in user.get('Attributes', []):
                user_data['attributes'][attr['Name']] = attr['Value']
            
            users.append(user_data)
        
        return {
            'users': users,
            'pagination_token': response.get('PaginationToken'),
            'count': len(users)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")


@router.get("/{username}")
async def get_cognito_user(
    username: str,
    current_admin: User = Depends(get_current_admin),
):
    """
    Get a specific user's details from Cognito (Admin only)
    """
    try:
        response = cognito_client.admin_get_user(
            UserPoolId=settings.cognito_user_pool_id,
            Username=username
        )
        
        user_data = {
            'username': response['Username'],
            'status': response['UserStatus'],
            'enabled': response['Enabled'],
            'created': response['UserCreateDate'].isoformat(),
            'modified': response['UserLastModifiedDate'].isoformat(),
            'attributes': {}
        }
        
        for attr in response.get('UserAttributes', []):
            user_data['attributes'][attr['Name']] = attr['Value']
        
        # Get user's groups
        groups_response = cognito_client.admin_list_groups_for_user(
            UserPoolId=settings.cognito_user_pool_id,
            Username=username
        )
        user_data['groups'] = [g['GroupName'] for g in groups_response.get('Groups', [])]
        
        return user_data
        
    except cognito_client.exceptions.UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")


@router.delete("/{username}")
async def delete_cognito_user(
    username: str,
    current_admin: User = Depends(get_current_admin),
):
    """
    Delete a user from Cognito (Admin only)
    """
    try:
        cognito_client.admin_delete_user(
            UserPoolId=settings.cognito_user_pool_id,
            Username=username
        )
        return {"message": f"User {username} deleted successfully"}
        
    except cognito_client.exceptions.UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")


@router.post("/{username}/enable")
async def enable_cognito_user(
    username: str,
    current_admin: User = Depends(get_current_admin),
):
    """
    Enable a disabled user in Cognito (Admin only)
    """
    try:
        cognito_client.admin_enable_user(
            UserPoolId=settings.cognito_user_pool_id,
            Username=username
        )
        return {"message": f"User {username} enabled successfully"}
        
    except cognito_client.exceptions.UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enabling user: {str(e)}")


@router.post("/{username}/disable")
async def disable_cognito_user(
    username: str,
    current_admin: User = Depends(get_current_admin),
):
    """
    Disable a user in Cognito (Admin only)
    """
    try:
        cognito_client.admin_disable_user(
            UserPoolId=settings.cognito_user_pool_id,
            Username=username
        )
        return {"message": f"User {username} disabled successfully"}
        
    except cognito_client.exceptions.UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disabling user: {str(e)}")


@router.post("/{username}/reset-password")
async def reset_user_password(
    username: str,
    current_admin: User = Depends(get_current_admin),
):
    """
    Reset a user's password and send them a new temporary password (Admin only)
    """
    try:
        cognito_client.admin_reset_user_password(
            UserPoolId=settings.cognito_user_pool_id,
            Username=username
        )
        return {"message": f"Password reset email sent to {username}"}
        
    except cognito_client.exceptions.UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting password: {str(e)}")


@router.post("/{username}/add-to-group")
async def add_user_to_group(
    username: str,
    group_name: str,
    current_admin: User = Depends(get_current_admin),
):
    """
    Add a user to a Cognito group (Admin only)
    """
    try:
        cognito_client.admin_add_user_to_group(
            UserPoolId=settings.cognito_user_pool_id,
            Username=username,
            GroupName=group_name
        )
        return {"message": f"User {username} added to group {group_name}"}
        
    except cognito_client.exceptions.UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except cognito_client.exceptions.ResourceNotFoundException:
        raise HTTPException(status_code=404, detail="Group not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding user to group: {str(e)}")


@router.post("/{username}/remove-from-group")
async def remove_user_from_group(
    username: str,
    group_name: str,
    current_admin: User = Depends(get_current_admin),
):
    """
    Remove a user from a Cognito group (Admin only)
    """
    try:
        cognito_client.admin_remove_user_from_group(
            UserPoolId=settings.cognito_user_pool_id,
            Username=username,
            GroupName=group_name
        )
        return {"message": f"User {username} removed from group {group_name}"}
        
    except cognito_client.exceptions.UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing user from group: {str(e)}")


@router.get("/groups/list")
async def list_groups(
    current_admin: User = Depends(get_current_admin),
):
    """
    List all Cognito groups (Admin only)
    """
    try:
        response = cognito_client.list_groups(
            UserPoolId=settings.cognito_user_pool_id,
            Limit=60
        )
        
        groups = []
        for group in response.get('Groups', []):
            groups.append({
                'name': group['GroupName'],
                'description': group.get('Description', ''),
                'created': group['CreationDate'].isoformat(),
                'modified': group['LastModifiedDate'].isoformat(),
            })
        
        return {'groups': groups}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing groups: {str(e)}")
