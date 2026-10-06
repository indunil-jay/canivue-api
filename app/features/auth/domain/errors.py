from dataclasses import dataclass
from typing import Any

from fastapi import status


@dataclass(frozen=True)
class DomainError:
    message: str
    code: str = "DOMAIN_ERROR"
    status_code: int = status.HTTP_400_BAD_REQUEST
    details: Any = None


@dataclass(frozen=True)
class ValidationErrorDomainError(DomainError):
    message: str = "Domain validation failed."
    code: str = "DOMAIN_VALIDATION_FAILED"
    status_code: int = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


@dataclass(frozen=True)
class InvalidEmailDomainError(ValidationErrorDomainError):
    message: str = "A valid email address is required."
    code: str = "INVALID_EMAIL"


@dataclass(frozen=True)
class WeakPasswordDomainError(ValidationErrorDomainError):
    message: str = "Password must be at least 8 characters long."
    code: str = "WEAK_PASSWORD"


@dataclass(frozen=True)
class EmptyPasswordHashDomainError(ValidationErrorDomainError):
    message: str = "Hashed password must not be empty."
    code: str = "EMPTY_PASSWORD_HASH"


@dataclass(frozen=True)
class UserAlreadyExistsDomainError(DomainError):
    message: str = "User already exists."
    code: str = "USER_ALREADY_EXISTS"
    status_code: int = status.HTTP_409_CONFLICT


@dataclass(frozen=True)
class UserNotFoundDomainError(DomainError):
    message: str = "User account not found."
    code: str = "USER_NOT_FOUND"
    status_code: int = status.HTTP_404_NOT_FOUND
