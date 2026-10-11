from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import Response

from app.config import settings
from app.core.file_storage import file_response, read_upload
from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.dogs.application.use_cases import (
    GetDogPhotoUseCase,
    GetDogUseCase,
    ListMyDogsUseCase,
    RegisterDogUseCase,
    RemoveDogPhotoUseCase,
    RemoveDogUseCase,
    SetDogPhotoUseCase,
    UpdateDogUseCase,
)
from app.features.dogs.presentation.dependencies import (
    get_get_dog_photo_use_case,
    get_get_dog_use_case,
    get_list_my_dogs_use_case,
    get_register_dog_use_case,
    get_remove_dog_photo_use_case,
    get_remove_dog_use_case,
    get_set_dog_photo_use_case,
    get_update_dog_use_case,
)
from app.features.dogs.presentation.schemas import DogCreateRequest, DogResponse, DogUpdateRequest
from app.shared.actor import Actor

router = APIRouter()


@router.post(
    "",
    response_model=APIResponse[DogResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a Dog for the current owner",
)
async def register_dog(
    payload: DogCreateRequest,
    actor: Actor = Depends(get_actor),
    use_case: RegisterDogUseCase = Depends(get_register_dog_use_case),
) -> APIResponse[DogResponse]:
    dog = await use_case.execute(actor, payload.to_domain())
    return APIResponse(message="Dog registered successfully", data=DogResponse.from_entity(dog))


@router.get("", response_model=APIResponse[list[DogResponse]], summary="List the owner's Dogs")
async def list_my_dogs(
    actor: Actor = Depends(get_actor),
    use_case: ListMyDogsUseCase = Depends(get_list_my_dogs_use_case),
) -> APIResponse[list[DogResponse]]:
    dogs = await use_case.execute(actor)
    return APIResponse(
        message="Dogs retrieved successfully", data=[DogResponse.from_entity(d) for d in dogs]
    )


@router.get("/{dog_id}", response_model=APIResponse[DogResponse], summary="Get one Dog's profile")
async def get_dog(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: GetDogUseCase = Depends(get_get_dog_use_case),
) -> APIResponse[DogResponse]:
    dog = await use_case.execute(actor, dog_id)
    return APIResponse(message="Dog retrieved successfully", data=DogResponse.from_entity(dog))


@router.patch("/{dog_id}", response_model=APIResponse[DogResponse], summary="Update a Dog")
async def update_dog(
    dog_id: str,
    payload: DogUpdateRequest,
    actor: Actor = Depends(get_actor),
    use_case: UpdateDogUseCase = Depends(get_update_dog_use_case),
) -> APIResponse[DogResponse]:
    dog = await use_case.execute(actor, dog_id, payload.to_domain())
    return APIResponse(message="Dog updated successfully", data=DogResponse.from_entity(dog))


@router.delete("/{dog_id}", response_model=APIResponse[None], summary="Remove a Dog")
async def remove_dog(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: RemoveDogUseCase = Depends(get_remove_dog_use_case),
) -> APIResponse[None]:
    await use_case.execute(actor, dog_id)
    return APIResponse(message="Dog removed successfully", data=None)


@router.put("/{dog_id}/photo", response_model=APIResponse[DogResponse], summary="Set a Dog's photo")
async def set_dog_photo(
    dog_id: str,
    file: UploadFile,
    actor: Actor = Depends(get_actor),
    use_case: SetDogPhotoUseCase = Depends(get_set_dog_photo_use_case),
) -> APIResponse[DogResponse]:
    dog = await use_case.execute(
        actor, dog_id, await read_upload(file), file.content_type, settings.MAX_UPLOAD_BYTES
    )
    return APIResponse(message="Dog photo updated successfully", data=DogResponse.from_entity(dog))


@router.get("/{dog_id}/photo", response_class=Response, summary="Download a Dog's photo")
async def get_dog_photo(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: GetDogPhotoUseCase = Depends(get_get_dog_photo_use_case),
) -> Response:
    return file_response(await use_case.execute(actor, dog_id))


@router.delete(
    "/{dog_id}/photo", response_model=APIResponse[DogResponse], summary="Remove a Dog's photo"
)
async def remove_dog_photo(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: RemoveDogPhotoUseCase = Depends(get_remove_dog_photo_use_case),
) -> APIResponse[DogResponse]:
    dog = await use_case.execute(actor, dog_id)
    return APIResponse(message="Dog photo removed successfully", data=DogResponse.from_entity(dog))
