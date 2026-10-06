from fastapi import APIRouter, Depends, status

from app.core.response import APIResponse
from app.features.auth.application.dtos import (
    LoginInputDTO,
    RegisterClientInputDTO,
    UserOutputDTO,
)
from app.features.auth.application.use_cases import LoginUseCase, RegisterClientUseCase
from app.features.auth.presentation.dependencies import (
    get_current_user,
    get_login_use_case,
    get_register_client_use_case,
)
from app.features.auth.presentation.schemas import (
    LoginRequest,
    LoginResponseData,
    RegisterClientRequest,
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

    data = UserResponseData(
        id=result.id,
        email=result.email,
        role=result.role.value,
        full_name=result.full_name,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )

    return APIResponse(
        success=True,
        message="Client account registered successfully",
        data=data,
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

    data = LoginResponseData(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        user=UserResponseData(
            id=result.user.id,
            email=result.user.email,
            role=result.user.role.value,
            full_name=result.user.full_name,
            is_active=result.user.is_active,
            created_at=result.user.created_at,
            updated_at=result.user.updated_at,
        ),
    )

    return APIResponse(
        success=True,
        message="Authentication successful",
        data=data,
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
    data = UserResponseData(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )

    return APIResponse(
        success=True,
        message="User profile retrieved successfully",
        data=data,
    )

