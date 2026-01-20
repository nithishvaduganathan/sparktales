"""Tests for group endpoints."""
import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str = "testuser@example.com") -> str:
    """Helper to register and login a user."""
    await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "TestPassword123",
            "full_name": "Test User",
        },
    )
    login_response = await client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "TestPassword123",
        },
    )
    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_public_group(client: AsyncClient):
    """Test creating a public group."""
    token = await get_auth_token(client, "group1@example.com")
    
    response = await client.post(
        "/api/groups/",
        json={
            "name": "Test Public Group",
            "description": "A test public group",
            "group_type": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Public Group"
    assert data["group_type"] == "public"
    assert data["member_count"] == 1  # Creator is automatically added


@pytest.mark.asyncio
async def test_create_private_group(client: AsyncClient):
    """Test creating a private group."""
    token = await get_auth_token(client, "group2@example.com")
    
    response = await client.post(
        "/api/groups/",
        json={
            "name": "Test Private Group",
            "description": "A test private group",
            "group_type": "private",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Private Group"
    assert data["group_type"] == "private"


@pytest.mark.asyncio
async def test_list_public_groups(client: AsyncClient):
    """Test listing public groups."""
    token = await get_auth_token(client, "group3@example.com")
    
    # Create a public group
    await client.post(
        "/api/groups/",
        json={
            "name": "Listed Public Group",
            "group_type": "public",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # List groups
    response = await client.get(
        "/api/groups/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_join_public_group(client: AsyncClient):
    """Test joining a public group."""
    # Create group with first user
    token1 = await get_auth_token(client, "groupowner@example.com")
    create_response = await client.post(
        "/api/groups/",
        json={
            "name": "Joinable Group",
            "group_type": "public",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    group_id = create_response.json()["id"]
    
    # Join with second user
    token2 = await get_auth_token(client, "joiner@example.com")
    response = await client.post(
        f"/api/groups/{group_id}/join",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_cannot_join_private_group_directly(client: AsyncClient):
    """Test that private groups cannot be joined directly."""
    # Create private group
    token1 = await get_auth_token(client, "privateowner@example.com")
    create_response = await client.post(
        "/api/groups/",
        json={
            "name": "Private Only Group",
            "group_type": "private",
        },
        headers={"Authorization": f"Bearer {token1}"},
    )
    group_id = create_response.json()["id"]
    
    # Try to join with second user
    token2 = await get_auth_token(client, "tryjoiner@example.com")
    response = await client.post(
        f"/api/groups/{group_id}/join",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_my_groups(client: AsyncClient):
    """Test listing user's groups."""
    token = await get_auth_token(client, "mygroups@example.com")
    
    # Create a group
    await client.post(
        "/api/groups/",
        json={"name": "My Test Group", "group_type": "public"},
        headers={"Authorization": f"Bearer {token}"},
    )
    
    # List my groups
    response = await client.get(
        "/api/groups/my-groups",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
