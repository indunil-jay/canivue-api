from typing import Any

from app.features.dogs.presentation.responses.dog_response import DogResponse


class DogsPresentationMapper:
    @staticmethod
    def to_dog_response(dog: Any) -> DogResponse:
        response = DogResponse.model_validate(dog)
        response.has_photo = dog.photo_file_id is not None
        return response
