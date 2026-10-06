from fastapi import APIRouter, Depends, status

from app.core.response import APIResponse
from app.features.auth.application.commands.create_client.create_client_command import (
    CreateClientCommand,
)
from app.features.auth.application.commands.create_client.create_client_command_handler import (
    CreateClientCommandHandler,
)
from app.features.auth.application.commands.create_staff.create_staff_command import (
    CreateStaffCommand,
)
from app.features.auth.application.commands.create_staff.create_staff_command_handler import (
    CreateStaffCommandHandler,
)
from app.features.auth.application.commands.login.login_user_command import (
    LoginUserCommand,
)
from app.features.auth.application.commands.login.login_user_command_handler import (
    LoginUserCommandHandler,
)
from app.features.auth.application.commands.rotate_token.rotate_refresh_token_command import (
    RotateRefreshTokenCommand,
)
from app.features.auth.application.commands.rotate_token.rotate_refresh_token_command_handler import (
    RotateRefreshTokenCommandHandler,
)
from app.features.auth.application.dtos.user_output_dto import UserOutputDTO
from app.features.auth.domain.enums.role import Role
from app.features.auth.presentation.dependencies import (
    get_create_client_command_handler,
    get_create_staff_command_handler,
    get_current_user,
    get_login_command_handler,
    get_rotate_token_command_handler,
    require_permissions,
)
from app.features.auth.presentation.mappers import AuthPresentationMapper
from app.features.auth.presentation.requests.create_staff_request import (
    CreateStaffRequest,
)
from app.features.auth.presentation.requests.login_request import LoginRequest
from app.features.auth.presentation.requests.refresh_token_request import (
    RefreshTokenRequest,
)
from app.features.auth.presentation.requests.register_client_request import (
    RegisterClientRequest,
)
from app.features.auth.presentation.responses.login_response import (
    LoginResponseData,
)
from app.features.auth.presentation.responses.token_pair_response import (
    TokenPairResponseData,
)
from app.features.auth.presentation.responses.user_response import (
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
    handler: CreateClientCommandHandler = Depends(get_create_client_command_handler),
) -> APIResponse[UserResponseData]:
    command = CreateClientCommand(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    result = await handler.handle(command)

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
    handler: LoginUserCommandHandler = Depends(get_login_command_handler),
) -> APIResponse[LoginResponseData]:
    command = LoginUserCommand(email=payload.email, password=payload.password)
    result = await handler.handle(command)

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
    handler: RotateRefreshTokenCommandHandler = Depends(get_rotate_token_command_handler),
) -> APIResponse[TokenPairResponseData]:
    command = RotateRefreshTokenCommand(refresh_token=payload.refresh_token)
    result = await handler.handle(command)

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
    handler: CreateStaffCommandHandler = Depends(get_create_staff_command_handler),
) -> APIResponse[UserResponseData]:
    command = CreateStaffCommand(
        email=payload.email,
        password=payload.password,
        role=Role(payload.role),
        full_name=payload.full_name,
    )
    result = await handler.handle(command)

    return APIResponse(
        success=True,
        message="Staff member created successfully",
        data=AuthPresentationMapper.to_user_response(result),
    )
