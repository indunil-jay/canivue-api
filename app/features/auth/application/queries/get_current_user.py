from app.features.auth.application.common_dtos import UserOutputDTO
from app.features.auth.application.queries.dtos import GetCurrentUserQuery
from app.features.auth.domain.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
)
from app.features.auth.domain.repositories import UserRepository


class GetCurrentUserUseCase:
    """Query Use Case to fetch an active authenticated user profile by user ID."""

    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def execute(self, query: GetCurrentUserQuery | int) -> UserOutputDTO:
        user_id = query.user_id if isinstance(query, GetCurrentUserQuery) else query
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise InvalidCredentialsError("User account not found.")

        if not user.is_active:
            raise AccountDisabledError()

        return UserOutputDTO(
            id=user.id,
            email=user.email,
            role=user.role,
            full_name=user.full_name,
            is_active=user.is_active,
            permissions=user.permissions,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
