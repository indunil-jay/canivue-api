from datetime import datetime, timedelta, timezone

from httpx import AsyncClient

from app.features.auth.application.commands.verify_email import verify_email_command_handler
from tests.helpers import PASSWORD, last_verification_code, login_headers, register_verified

EMAIL = "newowner@example.com"


async def _register(client: AsyncClient, email: str = EMAIL):
    resp = await client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert resp.status_code == 201
    return resp.json()["data"]


async def _verify(client: AsyncClient, code: str, email: str = EMAIL):
    return await client.post("/api/v1/auth/verify-email", json={"email": email, "code": code})


async def test_registration_sends_a_six_digit_code_and_leaves_email_unverified(client):
    user = await _register(client)

    assert user["is_email_verified"] is False
    code = last_verification_code(EMAIL)
    assert len(code) == 6 and code.isdigit()


async def test_login_is_refused_until_email_is_verified(client):
    await _register(client)

    resp = await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})

    assert resp.status_code == 403
    assert resp.json()["error"]["details"] == {"code": "EMAIL_NOT_VERIFIED"}


async def test_verifying_with_the_emailed_code_allows_login(client):
    await _register(client)

    resp = await _verify(client, last_verification_code(EMAIL))

    assert resp.status_code == 200
    assert resp.json()["data"]["is_email_verified"] is True
    assert await login_headers(client, EMAIL)


async def test_wrong_code_is_rejected(client):
    await _register(client)
    code = last_verification_code(EMAIL)
    wrong = "000000" if code != "000000" else "111111"

    resp = await _verify(client, wrong)

    assert resp.status_code == 401
    assert (
        await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    ).status_code == 403


async def test_code_cannot_be_used_twice(client):
    await _register(client)
    code = last_verification_code(EMAIL)
    assert (await _verify(client, code)).status_code == 200

    assert (await _verify(client, code)).status_code == 401


async def test_expired_code_is_rejected(client, monkeypatch):
    await _register(client)
    code = last_verification_code(EMAIL)
    later = datetime.now(timezone.utc) + timedelta(hours=1)
    monkeypatch.setattr(verify_email_command_handler, "_utc_now", lambda: later)

    assert (await _verify(client, code)).status_code == 401


async def test_code_is_locked_after_too_many_wrong_attempts(client):
    await _register(client)
    code = last_verification_code(EMAIL)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        await _verify(client, wrong)

    assert (await _verify(client, code)).status_code == 401


async def test_resend_issues_a_new_code_and_invalidates_the_old_one(client):
    await _register(client)
    old = last_verification_code(EMAIL)

    resp = await client.post("/api/v1/auth/resend-verification", json={"email": EMAIL})
    new = last_verification_code(EMAIL)

    assert resp.status_code == 200
    if new != old:
        assert (await _verify(client, old)).status_code == 401
    assert (await _verify(client, new)).status_code == 200


async def test_resend_for_unknown_email_does_not_reveal_anything(client):
    resp = await client.post(
        "/api/v1/auth/resend-verification", json={"email": "ghost@example.com"}
    )

    assert resp.status_code == 200


async def test_google_sign_in_is_verified_from_the_start(client):
    resp = await client.post(
        "/api/v1/auth/oauth/google", json={"id_token": "valid_google_token_newclient"}
    )

    assert resp.status_code == 200
    assert resp.json()["data"]["user"]["is_email_verified"] is True


async def test_helper_registers_a_verified_user(client):
    user = await register_verified(client, "helper@example.com")

    assert user["is_email_verified"] is True


async def test_google_sign_in_takes_over_an_unverified_account_and_drops_its_password(client):
    email = "linktarget@gmail.com"
    await _register(client, email)

    resp = await client.post(
        "/api/v1/auth/oauth/google", json={"id_token": "valid_google_token_linktarget"}
    )

    assert resp.status_code == 200
    assert resp.json()["data"]["user"]["is_email_verified"] is True
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 401
