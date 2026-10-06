from app.core.exceptions import AppException, ConflictException, ValidationException
from app.features.auth.domain.errors import (
    EmptyPasswordHashDomainError,
    InvalidEmailDomainError,
    UserAlreadyExistsDomainError,
    UserNotFoundDomainError,
    ValidationErrorDomainError,
    WeakPasswordDomainError,
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


class InvalidEmailError(ValidationException):
    def __init__(self, message: str = InvalidEmailDomainError.message):
        err = InvalidEmailDomainError(message=message)
        super().__init__(message=err.message)


class WeakPasswordError(ValidationException):
    def __init__(self, message: str = WeakPasswordDomainError.message):
        err = WeakPasswordDomainError(message=message)
        super().__init__(message=err.message)


class EmptyPasswordHashError(ValidationException):
    def __init__(self, message: str = EmptyPasswordHashDomainError.message):
        err = EmptyPasswordHashDomainError(message=message)
        super().__init__(message=err.message)
