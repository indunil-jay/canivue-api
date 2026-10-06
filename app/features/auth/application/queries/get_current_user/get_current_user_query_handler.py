from app.features.auth.application.dtos.user_output_dto import UserOutputDTO
from app.features.auth.application.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
)
from app.features.auth.application.interfaces.repositories.user_repository import (
    UserRepository,
)
from app.features.auth.application.mappers.user_dto_mapper import UserDTOMapper
from app.features.auth.application.queries.get_current_user.get_current_user_query import (
    GetCurrentUserQuery,
)


class GetCurrentUserQueryHandler:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def handle(self, query: GetCurrentUserQuery | int) -> UserOutputDTO:
        user_id = query.user_id if isinstance(query, GetCurrentUserQuery) else query
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountDisabledError()

        return UserDTOMapper.to_output_dto(user)
