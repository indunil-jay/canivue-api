from fastapi import APIRouter, Depends, status

from app.core.response import APIResponse
from app.features.auth.application.dtos import RegisterClientInputDTO
from app.features.auth.application.use_cases import RegisterClientUseCase
from app.features.auth.presentation.dependencies import get_register_client_use_case
from app.features.auth.presentation.schemas import RegisterClientRequest, UserResponseData

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
