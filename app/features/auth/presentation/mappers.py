from app.features.auth.application.dtos import LoginOutputDTO, TokenPairOutputDTO, UserOutputDTO
from app.features.auth.presentation.responses import (
    LoginResponseData,
    TokenPairResponseData,
    UserResponseData,
)


class AuthPresentationMapper:
    """Explicit mapper transforming Application DTOs to Presentation Response shapes."""

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
    def to_login_response(dto: LoginOutputDTO) -> LoginResponseData:
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
