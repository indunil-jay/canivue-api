from typing import List
from fastapi import APIRouter, Depends, Query, status

from app.core.response import APIResponse
from app.features.sample.application.dtos import CreateSampleDTO, UpdateSampleDTO
from app.features.sample.application.use_cases import (
    CreateSampleUseCase,
    DeleteSampleUseCase,
    GetSampleByIdUseCase,
    ListSamplesUseCase,
    UpdateSampleUseCase,
)
from app.features.sample.presentation.dependencies import (
    get_create_sample_use_case,
    get_delete_sample_use_case,
    get_get_sample_by_id_use_case,
    get_list_samples_use_case,
    get_update_sample_use_case,
)
from app.features.sample.presentation.schemas import (
    CreateSampleRequest,
    SampleResponse,
    UpdateSampleRequest,
)

router = APIRouter()


@router.post(
    "",
    response_model=APIResponse[SampleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sample item",
)
async def create_sample(
    request: CreateSampleRequest,
    use_case: CreateSampleUseCase = Depends(get_create_sample_use_case),
) -> APIResponse[SampleResponse]:
    dto = CreateSampleDTO(title=request.title, description=request.description)
    output = await use_case.execute(dto)
    return APIResponse(
        success=True,
        message="Sample created successfully",
        data=SampleResponse.model_validate(output),
    )


@router.get(
    "",
    response_model=APIResponse[List[SampleResponse]],
    summary="List all sample items",
)
async def list_samples(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Limit per page"),
    use_case: ListSamplesUseCase = Depends(get_list_samples_use_case),
) -> APIResponse[List[SampleResponse]]:
    outputs = await use_case.execute(skip=skip, limit=limit)
    return APIResponse(
        success=True,
        message="Samples retrieved successfully",
        data=[SampleResponse.model_validate(o) for o in outputs],
    )


@router.get(
    "/{sample_id}",
    response_model=APIResponse[SampleResponse],
    summary="Get sample item by ID",
)
async def get_sample_by_id(
    sample_id: str,
    use_case: GetSampleByIdUseCase = Depends(get_get_sample_by_id_use_case),
) -> APIResponse[SampleResponse]:
    output = await use_case.execute(sample_id=sample_id)
    return APIResponse(
        success=True,
        message="Sample retrieved successfully",
        data=SampleResponse.model_validate(output),
    )


@router.put(
    "/{sample_id}",
    response_model=APIResponse[SampleResponse],
    summary="Update sample item by ID",
)
async def update_sample(
    sample_id: str,
    request: UpdateSampleRequest,
    use_case: UpdateSampleUseCase = Depends(get_update_sample_use_case),
) -> APIResponse[SampleResponse]:
    dto = UpdateSampleDTO(
        title=request.title,
        description=request.description,
        is_active=request.is_active,
    )
    output = await use_case.execute(sample_id=sample_id, dto=dto)
    return APIResponse(
        success=True,
        message="Sample updated successfully",
        data=SampleResponse.model_validate(output),
    )


@router.delete(
    "/{sample_id}",
    response_model=APIResponse[dict],
    summary="Delete sample item by ID",
)
async def delete_sample(
    sample_id: str,
    use_case: DeleteSampleUseCase = Depends(get_delete_sample_use_case),
) -> APIResponse[dict]:
    await use_case.execute(sample_id=sample_id)
    return APIResponse(
        success=True,
        message="Sample deleted successfully",
        data={"sample_id": sample_id},
    )
