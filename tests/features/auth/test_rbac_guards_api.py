import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.infrastructure.seed import seed_rbac_catalog


@pytest.mark.asyncio
async def test_rbac_guards_and_admin_staff_provisioning(
    client: AsyncClient, db_session: AsyncSession
):
    """Admin can create staff members and role/permission guards correctly block/allow access."""
    # Seed default RBAC permissions and matrix
    await seed_rbac_catalog(db_session)

    # 1. Register a regular client user
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "regularclient@example.com", "password": "Password123!"},
    )
    assert reg_resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "regularclient@example.com", "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    client_data = login_resp.json()["data"]
    client_token = client_data["access_token"]
    # Check permissions list returned in login response
    assert "permissions" in client_data["user"]
    assert "dogs:read:own" in client_data["user"]["permissions"]
    assert "users:manage" not in client_data["user"]["permissions"]

    # 2. Try to access staff creation endpoint with CLIENT token -> should get 403 Forbidden
    client_headers = {"Authorization": f"Bearer {client_token}"}
    staff_payload = {
        "email": "dr.smith@clinic.com",
        "password": "VetPassword123!",
        "role": "VET",
        "full_name": "Dr. Smith",
    }
    forbidden_resp = await client.post(
        "/api/v1/auth/staff", json=staff_payload, headers=client_headers
    )
    assert forbidden_resp.status_code == 403
    assert (
        "permission" in forbidden_resp.json()["error"]["message"].lower()
        or "forbidden" in forbidden_resp.json()["error"]["message"].lower()
    )

    # 3. Create initial Admin user directly in DB (or via admin endpoint with ADMIN token)
    from app.features.auth.domain.entities.user import User
    from app.features.auth.domain.enums.role import Role
    from app.features.auth.infrastructure.repositories.user_repository import (
        SqlAlchemyUserRepository,
    )
    from app.features.auth.infrastructure.services.hasher import (
        Argon2PasswordHasher,
    )

    hasher = Argon2PasswordHasher()
    admin_user = User(
        id=None,
        email="admin@clinic.com",
        hashed_password=hasher.hash("AdminPass123!"),
        role=Role.ADMIN,
        full_name="Super Admin",
        is_active=True,
    )
    user_repo = SqlAlchemyUserRepository(session=db_session)
    await user_repo.create(admin_user)

    # Login as Admin
    admin_login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@clinic.com", "password": "AdminPass123!"},
    )
    assert admin_login_resp.status_code == 200
    admin_token = admin_login_resp.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    assert "users:manage" in admin_login_resp.json()["data"]["user"]["permissions"]

    # 4. Admin creates VET staff member
    create_staff_resp = await client.post(
        "/api/v1/auth/staff", json=staff_payload, headers=admin_headers
    )
    assert create_staff_resp.status_code == 201
    staff_data = create_staff_resp.json()["data"]
    assert staff_data["email"] == "dr.smith@clinic.com"
    assert staff_data["role"] == "VET"

    # 5. VET logs in and has veterinary permissions
    vet_login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "dr.smith@clinic.com", "password": "VetPassword123!"},
    )
    assert vet_login_resp.status_code == 200
    vet_perms = vet_login_resp.json()["data"]["user"]["permissions"]
    assert "assessments:review" in vet_perms
    assert "dogs:read:all" in vet_perms
    assert "users:manage" not in vet_perms
