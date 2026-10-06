from dataclasses import dataclass
from typing import Any

from fastapi import status


@dataclass(frozen=True)
class DomainError:
    """Base domain business rule violation error."""

    message: str
    code: str = "DOMAIN_ERROR"
    status_code: int = status.HTTP_400_BAD_REQUEST
    details: Any = None


@dataclass(frozen=True)
class UserAlreadyExistsDomainError(DomainError):
    message: str = "User already exists."
    code: str = "USER_ALREADY_EXISTS"
    status_code: int = status.HTTP_409_CONFLICT


@dataclass(frozen=True)
class InvalidCredentialsDomainError(DomainError):
    message: str = "Invalid email or password."
    code: str = "INVALID_CREDENTIALS"
    status_code: int = status.HTTP_401_UNAUTHORIZED


@dataclass(frozen=True)
class AccountDisabledDomainError(DomainError):
    message: str = "Account is disabled."
    code: str = "ACCOUNT_DISABLED"
    status_code: int = status.HTTP_403_FORBIDDEN


@dataclass(frozen=True)
class InsufficientPermissionsDomainError(DomainError):
    message: str = "Insufficient permissions to perform this action."
    code: str = "INSUFFICIENT_PERMISSIONS"
    status_code: int = status.HTTP_403_FORBIDDEN


@dataclass(frozen=True)
class TokenExpiredOrRevokedDomainError(DomainError):
    message: str = "Token is expired or revoked."
    code: str = "TOKEN_EXPIRED_OR_REVOKED"
    status_code: int = status.HTTP_401_UNAUTHORIZED


@dataclass(frozen=True)
class UserNotFoundDomainError(DomainError):
    message: str = "User account not found."
    code: str = "USER_NOT_FOUND"
    status_code: int = status.HTTP_404_NOT_FOUND


@dataclass(frozen=True)
class ValidationErrorDomainError(DomainError):
    message: str = "Validation failed."
    code: str = "VALIDATION_FAILED"
    status_code: int = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
