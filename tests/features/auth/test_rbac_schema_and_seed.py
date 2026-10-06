import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.domain.enums.role import Role
from app.features.auth.infrastructure.repositories.rbac_repository import (
    SqlAlchemyRbacRepository,
)
from app.features.auth.infrastructure.seed import seed_rbac_catalog


@pytest.mark.asyncio
async def test_seed_rbac_catalog_and_query_permissions(db_session: AsyncSession):
    """Seed utility populates permissions and maps them to ADMIN, VET, and CLIENT roles."""
    await seed_rbac_catalog(db_session)

    rbac_repo = SqlAlchemyRbacRepository(session=db_session)

    admin_perms = await rbac_repo.get_permissions_for_role(Role.ADMIN)
    vet_perms = await rbac_repo.get_permissions_for_role(Role.VET)
    client_perms = await rbac_repo.get_permissions_for_role(Role.CLIENT)

    # Client permissions check
    assert "dogs:read:own" in client_perms
    assert "assessments:create" in client_perms
    assert "users:manage" not in client_perms

    # Vet permissions check
    assert "dogs:read:all" in vet_perms
    assert "assessments:review" in vet_perms
    assert "users:manage" not in vet_perms

    # Admin permissions check
    assert "users:manage" in admin_perms
    assert "roles:manage" in admin_perms
    assert "assessments:review" in admin_perms
    assert "dogs:read:all" in admin_perms


@pytest.mark.asyncio
async def test_seed_idempotency(db_session: AsyncSession):
    """Running the seed catalog multiple times should not cause duplicate errors."""
    await seed_rbac_catalog(db_session)
    await seed_rbac_catalog(db_session)

    rbac_repo = SqlAlchemyRbacRepository(session=db_session)
    client_perms = await rbac_repo.get_permissions_for_role(Role.CLIENT)
    assert len(client_perms) > 0
