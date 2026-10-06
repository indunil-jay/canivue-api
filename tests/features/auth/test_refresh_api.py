import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_refresh_token_rotation_success(client: AsyncClient):
    """User can exchange a valid refresh token for a new token pair, and the old token is revoked."""
    # 1. Register & Login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "refresher@example.com", "password": "Password123!"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresher@example.com", "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    first_tokens = login_resp.json()["data"]
    refresh_token_1 = first_tokens["refresh_token"]

    # 2. Use refresh token 1 to get new tokens
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token_1},
    )
    assert refresh_resp.status_code == 200
    second_tokens = refresh_resp.json()["data"]
    assert "access_token" in second_tokens
    assert "refresh_token" in second_tokens
    refresh_token_2 = second_tokens["refresh_token"]
    assert refresh_token_2 != refresh_token_1

    # 3. New access token works against /me
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {second_tokens['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == "refresher@example.com"

    # 4. Old refresh token 1 is now revoked and cannot be reused
    reuse_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token_1},
    )
    assert reuse_resp.status_code == 401
    assert (
        "revoked" in reuse_resp.json()["error"]["message"].lower()
        or "expired" in reuse_resp.json()["error"]["message"].lower()
    )


@pytest.mark.asyncio
async def test_refresh_token_invalid_or_garbage_token_fails(client: AsyncClient):
    """Submitting an invalid refresh token returns 401 Unauthorized."""
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "garbage.token.here"},
    )
    assert resp.status_code == 401
