"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPassword123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert data["role"] == "student"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email."""
    # First registration
    await client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "TestPassword123",
            "full_name": "First User",
        },
    )
    
    # Second registration with same email
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "TestPassword123",
            "full_name": "Second User",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login."""
    # Register user first
    await client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "password": "TestPassword123",
            "full_name": "Login User",
        },
    )
    
    # Login
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "TestPassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Test login with wrong password."""
    # Register user first
    await client.post(
        "/api/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "TestPassword123",
            "full_name": "Wrong Pass User",
        },
    )
    
    # Login with wrong password
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "WrongPassword123",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    """Test getting current user profile."""
    # Register user
    await client.post(
        "/api/auth/register",
        json={
            "email": "profile@example.com",
            "password": "TestPassword123",
            "full_name": "Profile User",
        },
    )
    
    # Login to get token
    login_response = await client.post(
        "/api/auth/login",
        json={
            "email": "profile@example.com",
            "password": "TestPassword123",
        },
    )
    token = login_response.json()["access_token"]
    
    # Get profile
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile@example.com"
    assert data["full_name"] == "Profile User"
