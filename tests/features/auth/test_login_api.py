import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success_and_get_me(client: AsyncClient):
    """User can log in with valid credentials and use the bearer token to query /me."""
    # 1. Register user
    reg_payload = {
        "email": "loginuser@example.com",
        "password": "ValidPassword123!",
        "full_name": "Login Tester",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201

    # 2. Login
    login_payload = {
        "email": "loginuser@example.com",
        "password": "ValidPassword123!",
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["success"] is True
    assert "access_token" in login_data["data"]
    assert "refresh_token" in login_data["data"]
    assert login_data["data"]["token_type"] == "bearer"
    assert login_data["data"]["user"]["email"] == "loginuser@example.com"
    access_token = login_data["data"]["access_token"]

    # 3. Call /me with Bearer token
    headers = {"Authorization": f"Bearer {access_token}"}
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["success"] is True
    assert me_data["data"]["email"] == "loginuser@example.com"
    assert me_data["data"]["role"] == "CLIENT"


@pytest.mark.asyncio
async def test_login_invalid_password_fails(client: AsyncClient):
    """Logging in with incorrect password returns 401 Unauthorized."""
    reg_payload = {
        "email": "wrongpwd@example.com",
        "password": "ValidPassword123!",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrongpwd@example.com",
        "password": "WrongPassword999!",
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 401
    assert login_resp.json()["success"] is False


@pytest.mark.asyncio
async def test_login_nonexistent_user_fails(client: AsyncClient):
    """Logging in with non-existent email returns 401 Unauthorized."""
    login_payload = {
        "email": "nobody@example.com",
        "password": "SomePassword123!",
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 401
    assert login_resp.json()["success"] is False


@pytest.mark.asyncio
async def test_get_me_unauthorized_without_token(client: AsyncClient):
    """Accessing /me without Authorization header returns 401."""
    me_resp = await client.get("/api/v1/auth/me")
    assert me_resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token_fails(client: AsyncClient):
    """Accessing /me with invalid token returns 401."""
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 401
