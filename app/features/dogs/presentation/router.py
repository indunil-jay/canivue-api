from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import Response

from app.config import settings
from app.core.file_storage import file_response, read_upload
from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.dogs.application.commands.register_dog.register_dog_command import (
    RegisterDogCommand,
)
from app.features.dogs.application.commands.register_dog.register_dog_command_handler import (
    RegisterDogCommandHandler,
)
from app.features.dogs.application.commands.remove_dog.remove_dog_command import RemoveDogCommand
from app.features.dogs.application.commands.remove_dog.remove_dog_command_handler import (
    RemoveDogCommandHandler,
)
from app.features.dogs.application.commands.remove_dog_photo.remove_dog_photo_command import (
    RemoveDogPhotoCommand,
)
from app.features.dogs.application.commands.remove_dog_photo.remove_dog_photo_command_handler import (
    RemoveDogPhotoCommandHandler,
)
from app.features.dogs.application.commands.set_dog_photo.set_dog_photo_command import (
    SetDogPhotoCommand,
)
from app.features.dogs.application.commands.set_dog_photo.set_dog_photo_command_handler import (
    SetDogPhotoCommandHandler,
)
from app.features.dogs.application.commands.update_dog.update_dog_command import UpdateDogCommand
from app.features.dogs.application.commands.update_dog.update_dog_command_handler import (
    UpdateDogCommandHandler,
)
from app.features.dogs.application.queries.get_dog.get_dog_query import GetDogQuery
from app.features.dogs.application.queries.get_dog.get_dog_query_handler import GetDogQueryHandler
from app.features.dogs.application.queries.get_dog_photo.get_dog_photo_query import GetDogPhotoQuery
from app.features.dogs.application.queries.get_dog_photo.get_dog_photo_query_handler import (
    GetDogPhotoQueryHandler,
)
from app.features.dogs.application.queries.list_my_dogs.list_my_dogs_query import ListMyDogsQuery
from app.features.dogs.application.queries.list_my_dogs.list_my_dogs_query_handler import (
    ListMyDogsQueryHandler,
)
from app.features.dogs.presentation.dependencies import (
    get_dog_photo_query_handler,
    get_dog_query_handler,
    get_list_my_dogs_query_handler,
    get_register_dog_command_handler,
    get_remove_dog_command_handler,
    get_remove_dog_photo_command_handler,
    get_set_dog_photo_command_handler,
    get_update_dog_command_handler,
)
from app.features.dogs.presentation.mappers import DogsPresentationMapper
from app.features.dogs.presentation.requests.dog_create_request import DogCreateRequest
from app.features.dogs.presentation.requests.dog_update_request import DogUpdateRequest
from app.features.dogs.presentation.responses.dog_response import DogResponse
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
    handler: RegisterDogCommandHandler = Depends(get_register_dog_command_handler),
) -> APIResponse[DogResponse]:
    dog = await handler.handle(RegisterDogCommand(actor=actor, attributes=payload.to_domain()))
    return APIResponse(
        message="Dog registered successfully", data=DogsPresentationMapper.to_dog_response(dog)
    )


@router.get("", response_model=APIResponse[list[DogResponse]], summary="List the owner's Dogs")
async def list_my_dogs(
    actor: Actor = Depends(get_actor),
    handler: ListMyDogsQueryHandler = Depends(get_list_my_dogs_query_handler),
) -> APIResponse[list[DogResponse]]:
    dogs = await handler.handle(ListMyDogsQuery(actor=actor))
    return APIResponse(
        message="Dogs retrieved successfully",
        data=[DogsPresentationMapper.to_dog_response(d) for d in dogs],
    )


@router.get("/{dog_id}", response_model=APIResponse[DogResponse], summary="Get one Dog's profile")
async def get_dog(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: GetDogQueryHandler = Depends(get_dog_query_handler),
) -> APIResponse[DogResponse]:
    dog = await handler.handle(GetDogQuery(actor=actor, dog_id=dog_id))
    return APIResponse(
        message="Dog retrieved successfully", data=DogsPresentationMapper.to_dog_response(dog)
    )


@router.patch("/{dog_id}", response_model=APIResponse[DogResponse], summary="Update a Dog")
async def update_dog(
    dog_id: str,
    payload: DogUpdateRequest,
    actor: Actor = Depends(get_actor),
    handler: UpdateDogCommandHandler = Depends(get_update_dog_command_handler),
) -> APIResponse[DogResponse]:
    dog = await handler.handle(
        UpdateDogCommand(actor=actor, dog_id=dog_id, changes=payload.to_domain())
    )
    return APIResponse(
        message="Dog updated successfully", data=DogsPresentationMapper.to_dog_response(dog)
    )


@router.delete("/{dog_id}", response_model=APIResponse[None], summary="Remove a Dog")
async def remove_dog(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: RemoveDogCommandHandler = Depends(get_remove_dog_command_handler),
) -> APIResponse[None]:
    await handler.handle(RemoveDogCommand(actor=actor, dog_id=dog_id))
    return APIResponse(message="Dog removed successfully", data=None)


@router.put("/{dog_id}/photo", response_model=APIResponse[DogResponse], summary="Set a Dog's photo")
async def set_dog_photo(
    dog_id: str,
    file: UploadFile,
    actor: Actor = Depends(get_actor),
    handler: SetDogPhotoCommandHandler = Depends(get_set_dog_photo_command_handler),
) -> APIResponse[DogResponse]:
    dog = await handler.handle(
        SetDogPhotoCommand(
            actor=actor,
            dog_id=dog_id,
            content=await read_upload(file),
            content_type=file.content_type,
            max_bytes=settings.MAX_UPLOAD_BYTES,
        )
    )
    return APIResponse(
        message="Dog photo updated successfully", data=DogsPresentationMapper.to_dog_response(dog)
    )


@router.get("/{dog_id}/photo", response_class=Response, summary="Download a Dog's photo")
async def get_dog_photo(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: GetDogPhotoQueryHandler = Depends(get_dog_photo_query_handler),
) -> Response:
    return file_response(await handler.handle(GetDogPhotoQuery(actor=actor, dog_id=dog_id)))


@router.delete(
    "/{dog_id}/photo", response_model=APIResponse[DogResponse], summary="Remove a Dog's photo"
)
async def remove_dog_photo(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: RemoveDogPhotoCommandHandler = Depends(get_remove_dog_photo_command_handler),
) -> APIResponse[DogResponse]:
    dog = await handler.handle(RemoveDogPhotoCommand(actor=actor, dog_id=dog_id))
    return APIResponse(
        message="Dog photo removed successfully", data=DogsPresentationMapper.to_dog_response(dog)
    )
