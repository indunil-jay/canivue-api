from fastapi import APIRouter, Depends, status

from app.core.response import APIResponse
from app.features.auth.application.dtos import (
    CreateStaffInputDTO,
    LoginInputDTO,
    RefreshTokenInputDTO,
    RegisterClientInputDTO,
    UserOutputDTO,
)
from app.features.auth.application.use_cases import (
    CreateStaffUserUseCase,
    LoginUseCase,
    RefreshTokenUseCase,
    RegisterClientUseCase,
)
from app.features.auth.domain.entities import Role
from app.features.auth.presentation.dependencies import (
    get_create_staff_use_case,
    get_current_user,
    get_login_use_case,
    get_refresh_token_use_case,
    get_register_client_use_case,
    require_permissions,
)
from app.features.auth.presentation.mappers import AuthPresentationMapper
from app.features.auth.presentation.requests import (
    CreateStaffRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterClientRequest,
)
from app.features.auth.presentation.responses import (
    LoginResponseData,
    TokenPairResponseData,
    UserResponseData,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=APIResponse[UserResponseData],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new client account",
    description="Allows public users to create a new client account. Defaults strictly to CLIENT role.",
)
async def register_client(
    payload: RegisterClientRequest,
    use_case: RegisterClientUseCase = Depends(get_register_client_use_case),
) -> APIResponse[UserResponseData]:
    dto = RegisterClientInputDTO(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    result = await use_case.execute(dto)

    return APIResponse(
        success=True,
        message="Client account registered successfully",
        data=AuthPresentationMapper.to_user_response(result),
    )


@router.post(
    "/login",
    response_model=APIResponse[LoginResponseData],
    status_code=status.HTTP_200_OK,
    summary="User login with email and password",
    description="Authenticates credentials and issues access and refresh JWT tokens.",
)
async def login(
    payload: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case),
) -> APIResponse[LoginResponseData]:
    dto = LoginInputDTO(email=payload.email, password=payload.password)
    result = await use_case.execute(dto)

    return APIResponse(
        success=True,
        message="Authentication successful",
        data=AuthPresentationMapper.to_login_response(result),
    )


@router.post(
    "/refresh",
    response_model=APIResponse[TokenPairResponseData],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token with refresh token rotation",
    description="Validates the refresh token, revokes it, and issues a new access/refresh token pair.",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    use_case: RefreshTokenUseCase = Depends(get_refresh_token_use_case),
) -> APIResponse[TokenPairResponseData]:
    dto = RefreshTokenInputDTO(refresh_token=payload.refresh_token)
    result = await use_case.execute(dto)

    return APIResponse(
        success=True,
        message="Tokens refreshed successfully",
        data=AuthPresentationMapper.to_token_pair_response(result),
    )


@router.get(
    "/me",
    response_model=APIResponse[UserResponseData],
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
    description="Returns the profile and role of the currently authenticated user.",
)
async def get_me(
    current_user: UserOutputDTO = Depends(get_current_user),
) -> APIResponse[UserResponseData]:
    return APIResponse(
        success=True,
        message="User profile retrieved successfully",
        data=AuthPresentationMapper.to_user_response(current_user),
    )


@router.post(
    "/staff",
    response_model=APIResponse[UserResponseData],
    status_code=status.HTTP_201_CREATED,
    summary="Create a staff user account (VET or ADMIN)",
    description="Onboards a veterinary or administrative staff account. Requires 'users:manage' permission.",
)
async def create_staff(
    payload: CreateStaffRequest,
    current_user: UserOutputDTO = Depends(require_permissions("users:manage")),
    use_case: CreateStaffUserUseCase = Depends(get_create_staff_use_case),
) -> APIResponse[UserResponseData]:
    dto = CreateStaffInputDTO(
        email=payload.email,
        password=payload.password,
        role=Role(payload.role),
        full_name=payload.full_name,
    )
    result = await use_case.execute(dto)

    return APIResponse(
        success=True,
        message="Staff member created successfully",
        data=AuthPresentationMapper.to_user_response(result),
    )



