from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.domain.entities.user import User
from app.features.auth.domain.enums.role import Role
from app.features.auth.infrastructure.persistence.repositories.user_repository import (
    SqlAlchemyUserRepository,
)
from app.features.auth.infrastructure.services.hasher import Argon2PasswordHasher
from app.features.auth.presentation.dependencies import _email_service_instance

PASSWORD = "Password123!"


def last_verification_code(email: str) -> str:
    for sent in reversed(_email_service_instance.sent_emails):
        if sent["to"] == email and "code" in sent:
            return sent["code"]
    raise AssertionError(f"No verification code was sent to {email}")


async def verify_email(client: AsyncClient, email: str) -> dict:
    verify = await client.post(
        "/api/v1/auth/verify-email",
        json={"email": email, "code": last_verification_code(email)},
    )
    assert verify.status_code == 200, verify.text
    return verify.json()["data"]


async def register_verified(
    client: AsyncClient, email: str, password: str = PASSWORD, **extra
) -> dict:
    resp = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password, **extra}
    )
    assert resp.status_code == 201, resp.text
    return await verify_email(client, email)


async def login_headers(client: AsyncClient, email: str, password: str = PASSWORD) -> dict:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}


async def owner_headers(client: AsyncClient, email: str = "owner@example.com", **extra) -> dict:
    await register_verified(client, email, **extra)
    return await login_headers(client, email)


async def admin_headers(
    client: AsyncClient, db_session: AsyncSession, email: str = "admin@example.com"
) -> dict:
    await SqlAlchemyUserRepository(session=db_session).create(
        User(
            id=None,
            email=email,
            hashed_password=Argon2PasswordHasher().hash(PASSWORD),
            role=Role.ADMIN,
            full_name="Admin",
        )
    )
    return await login_headers(client, email)


async def vet_headers(client: AsyncClient, email: str = "vet@example.com", **extra) -> dict:
    await register_verified(client, email, role="VET", **extra)
    return await login_headers(client, email)


async def verified_vet(
    client: AsyncClient,
    db_session: AsyncSession,
    email: str = "vet@example.com",
    full_name: str = "Dr. Sarah Jenkins",
    **profile,
) -> tuple[dict, str]:
    """A veterinarian an admin has verified. Returns (auth headers, veterinarian id)."""
    headers = await vet_headers(client, email, full_name=full_name)
    profile.setdefault("consultation_fee_usd", 40.0)
    resp = await client.patch("/api/v1/veterinarians/me", headers=headers, json=profile)
    assert resp.status_code == 200, resp.text
    vet_id = resp.json()["data"]["id"]
    admin = await admin_headers(client, db_session, f"admin-for-{email}")
    verify = await client.post(f"/api/v1/veterinarians/{vet_id}/verify", headers=admin)
    assert verify.status_code == 200, verify.text
    return headers, vet_id
