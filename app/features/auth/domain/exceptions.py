from app.core.exceptions import AppException, ConflictException, ValidationException
from app.features.auth.domain.errors import (
    UserAlreadyExistsDomainError,
    UserNotFoundDomainError,
    ValidationErrorDomainError,
)


class UserAlreadyExistsError(ConflictException):
    def __init__(self, email: str):
        err = UserAlreadyExistsDomainError(message=f"User with email '{email}' already exists.")
        super().__init__(message=err.message)


class UserNotFoundError(AppException):
    def __init__(self, message: str = UserNotFoundDomainError.message):
        err = UserNotFoundDomainError(message=message)
        super().__init__(message=err.message, status_code=err.status_code)


class DomainValidationException(ValidationException):
    def __init__(self, message: str = ValidationErrorDomainError.message):
        err = ValidationErrorDomainError(message=message)
        super().__init__(message=err.message)
