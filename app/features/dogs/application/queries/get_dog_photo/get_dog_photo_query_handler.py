from app.features.dogs.application.queries.get_dog_photo.get_dog_photo_query import GetDogPhotoQuery
from app.features.dogs.application.services.dog_access import DogAccess
from app.shared.files import (
    FileContent,
    FileStorageProtocol,
    StoredFileNotFoundError,
)


class GetDogPhotoQueryHandler:
    def __init__(self, access: DogAccess, storage: FileStorageProtocol):
        self._access = access
        self._storage = storage

    async def handle(self, query: GetDogPhotoQuery) -> FileContent:
        dog = await self._access.readable(query.actor, query.dog_id)
        if not dog.photo_file_id:
            raise StoredFileNotFoundError()
        return await self._storage.load(dog.photo_file_id)
