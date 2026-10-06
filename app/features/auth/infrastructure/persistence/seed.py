from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.domain.enums.role import Role
from app.features.auth.infrastructure.persistence.repositories.rbac_repository import (
    SqlAlchemyRbacRepository,
)

DEFAULT_PERMISSIONS: dict[str, str] = {
    # Dogs
    "dogs:read:own": "Read personal dogs",
    "dogs:write:own": "Register and update personal dogs",
    "dogs:read:all": "Read any dog profile across the clinic",
    "dogs:write:all": "Update any dog profile across the clinic",
    # Assessments
    "assessments:create": "Submit a diagnostic assessment session",
    "assessments:read:own": "Read personal dog assessment reports",
    "assessments:review": "Review clinical assessments and render veterinary diagnoses",
    # Admin / System
    "users:manage": "Create and manage system user accounts",
    "roles:manage": "Manage system roles and permissions",
}

ROLE_PERMISSION_MATRIX: dict[Role, list[str]] = {
    Role.CLIENT: [
        "dogs:read:own",
        "dogs:write:own",
        "assessments:create",
        "assessments:read:own",
    ],
    Role.VET: [
        "dogs:read:own",
        "dogs:write:own",
        "dogs:read:all",
        "dogs:write:all",
        "assessments:create",
        "assessments:read:own",
        "assessments:review",
    ],
    Role.ADMIN: [
        "dogs:read:own",
        "dogs:write:own",
        "dogs:read:all",
        "dogs:write:all",
        "assessments:create",
        "assessments:read:own",
        "assessments:review",
        "users:manage",
        "roles:manage",
    ],
}


async def seed_rbac_catalog(session: AsyncSession) -> None:
    rbac_repo = SqlAlchemyRbacRepository(session=session)

    # 1. Seed all permissions
    for perm_name, desc in DEFAULT_PERMISSIONS.items():
        await rbac_repo.create_permission_if_not_exists(name=perm_name, description=desc)

    # 2. Seed role assignments
    for role, perms in ROLE_PERMISSION_MATRIX.items():
        for perm_name in perms:
            await rbac_repo.assign_permission_to_role(role=role, permission_name=perm_name)
