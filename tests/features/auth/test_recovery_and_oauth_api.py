import pytest
from httpx import AsyncClient

from app.features.auth.presentation.dependencies import (
    _email_service_instance,
)


@pytest.mark.asyncio
async def test_forgot_and_reset_password_flow(client: AsyncClient):
    # 1. Register a test user
    reg_payload = {
        "email": "resetme@example.com",
        "password": "InitialPassword123!",
        "full_name": "Reset Tester",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201

    # Login to create an active refresh token
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "resetme@example.com", "password": "InitialPassword123!"},
    )
    assert login_resp.status_code == 200
    old_refresh_token = login_resp.json()["data"]["refresh_token"]

    # 2. Request password reset
    forgot_resp = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "resetme@example.com"},
    )
    assert forgot_resp.status_code == 200
    assert forgot_resp.json()["success"] is True

    # Check that email service captured the reset token
    assert len(_email_service_instance.sent_emails) > 0
    last_email = _email_service_instance.sent_emails[-1]
    assert last_email["to"] == "resetme@example.com"
    token = last_email["token"]

    # 3. Reset password with new password
    reset_resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "NewSecurePassword999!"},
    )
    assert reset_resp.status_code == 200
    assert reset_resp.json()["success"] is True

    # 4. Old password fails
    old_login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "resetme@example.com", "password": "InitialPassword123!"},
    )
    assert old_login_resp.status_code == 401

    # 5. New password succeeds
    new_login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "resetme@example.com", "password": "NewSecurePassword999!"},
    )
    assert new_login_resp.status_code == 200

    # 6. Old refresh token is revoked
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert refresh_resp.status_code == 401


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email_returns_success(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "unknown_user_999@example.com"},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_reset_password_with_invalid_token_fails(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid_fake_token", "new_password": "NewValidPassword123!"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_google_oauth_new_user_provisioning(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/oauth/google",
        json={"id_token": "valid_google_token_newclient"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "newclient@gmail.com"
    assert data["user"]["role"] == "CLIENT"


@pytest.mark.asyncio
async def test_google_oauth_existing_user_linking(client: AsyncClient):
    reg_payload = {
        "email": "linktarget@gmail.com",
        "password": "LocalPassword123!",
        "full_name": "Local Account",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    resp = await client.post(
        "/api/v1/auth/oauth/google",
        json={"id_token": "valid_google_token_linktarget"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["user"]["email"] == "linktarget@gmail.com"

    # User can still log in with their local password
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "linktarget@gmail.com", "password": "LocalPassword123!"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_google_oauth_invalid_token_fails(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/oauth/google",
        json={"id_token": "invalid_or_garbage_google_token"},
    )
    assert resp.status_code == 401
