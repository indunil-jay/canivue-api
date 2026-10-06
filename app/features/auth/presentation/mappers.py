from app.features.auth.application.dtos.login_result_dto import LoginResultDTO
from app.features.auth.application.dtos.token_pair_output_dto import (
    TokenPairOutputDTO,
)
from app.features.auth.application.dtos.user_output_dto import UserOutputDTO
from app.features.auth.presentation.responses.login_response import (
    LoginResponseData,
)
from app.features.auth.presentation.responses.token_pair_response import (
    TokenPairResponseData,
)
from app.features.auth.presentation.responses.user_response import (
    UserResponseData,
)


class AuthPresentationMapper:
    @staticmethod
    def to_user_response(dto: UserOutputDTO) -> UserResponseData:
        return UserResponseData(
            id=dto.id,
            email=dto.email,
            role=dto.role.value,
            full_name=dto.full_name,
            is_active=dto.is_active,
            permissions=dto.permissions,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    @staticmethod
    def to_login_response(dto: LoginResultDTO) -> LoginResponseData:
        return LoginResponseData(
            access_token=dto.access_token,
            refresh_token=dto.refresh_token,
            token_type=dto.token_type,
            user=AuthPresentationMapper.to_user_response(dto.user),
        )

    @staticmethod
    def to_token_pair_response(dto: TokenPairOutputDTO) -> TokenPairResponseData:
        return TokenPairResponseData(
            access_token=dto.access_token,
            refresh_token=dto.refresh_token,
            token_type=dto.token_type,
        )
