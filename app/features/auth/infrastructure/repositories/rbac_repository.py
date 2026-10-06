from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.application.interfaces.repositories.rbac_repository import (
    RbacRepository,
)
from app.features.auth.domain.enums.role import Role
from app.features.auth.infrastructure.models.permission_model import (
    PermissionModel,
)
from app.features.auth.infrastructure.models.role_permission_model import (
    RolePermissionModel,
)


class SqlAlchemyRbacRepository(RbacRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_permissions_for_role(self, role: Role | str) -> list[str]:
        role_str = role.value if isinstance(role, Role) else str(role)

        stmt = (
            select(PermissionModel.name)
            .join(RolePermissionModel, RolePermissionModel.permission_id == PermissionModel.id)
            .where(RolePermissionModel.role == role_str)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_permission_if_not_exists(
        self, name: str, description: str | None = None
    ) -> int:
        stmt = select(PermissionModel).where(PermissionModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            model = PermissionModel(name=name, description=description)
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
        return model.id

    async def assign_permission_to_role(self, role: Role | str, permission_name: str) -> None:
        role_str = role.value if isinstance(role, Role) else str(role)
        perm_id = await self.create_permission_if_not_exists(permission_name)

        stmt = select(RolePermissionModel).where(
            RolePermissionModel.role == role_str,
            RolePermissionModel.permission_id == perm_id,
        )
        result = await self._session.execute(stmt)
        exists = result.scalar_one_or_none()
        if not exists:
            link = RolePermissionModel(role=role_str, permission_id=perm_id)
            self._session.add(link)
            await self._session.flush()
