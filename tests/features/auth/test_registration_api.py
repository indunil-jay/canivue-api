import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_client_success(client: AsyncClient):
    """Registering a new client returns 201 Created and user profile."""
    payload = {
        "email": "testowner@example.com",
        "password": "Password123!",
        "full_name": "John Doe",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "testowner@example.com"
    assert body["data"]["full_name"] == "John Doe"
    assert body["data"]["role"] == "CLIENT"
    assert body["data"]["is_active"] is True
    assert "password" not in body["data"]
    assert "hashed_password" not in body["data"]


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client: AsyncClient):
    """Attempting to register with an existing email returns 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "First User",
    }
    resp1 = await client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
    body = resp2.json()
    assert body["success"] is False
    assert "already exists" in body["error"]["message"].lower()


@pytest.mark.asyncio
async def test_register_invalid_email_fails(client: AsyncClient):
    """Attempting to register with an invalid email returns 422 Unprocessable Entity."""
    payload = {
        "email": "not-an-email",
        "password": "Password123!",
        "full_name": "Test User",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
