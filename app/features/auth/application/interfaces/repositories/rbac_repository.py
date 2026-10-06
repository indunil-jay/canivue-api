from abc import ABC, abstractmethod


class RbacRepository(ABC):
    @abstractmethod
    async def get_permissions_for_role(self, role: str) -> list[str]: ...

    @abstractmethod
    async def assign_permission_to_role(self, role: str, permission_name: str) -> None: ...

    @abstractmethod
    async def create_permission_if_not_exists(
        self, name: str, description: str | None = None
    ) -> int: ...
