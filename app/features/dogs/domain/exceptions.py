from app.core.exceptions import NotFoundException, ValidationException


class DogNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Dog not found.")


class InvalidDogError(ValidationException):
    pass
