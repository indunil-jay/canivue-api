from dataclasses import dataclass
from typing import Any

from fastapi import status


@dataclass(frozen=True)
class ApplicationError:
    message: str
    code: str = "APPLICATION_ERROR"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    details: Any = None


@dataclass(frozen=True)
class InvalidCredentialsApplicationError(ApplicationError):
    message: str = "Invalid email or password."
    code: str = "INVALID_CREDENTIALS"
    status_code: int = status.HTTP_401_UNAUTHORIZED


@dataclass(frozen=True)
class AccountDisabledApplicationError(ApplicationError):
    message: str = "Account is disabled."
    code: str = "ACCOUNT_DISABLED"
    status_code: int = status.HTTP_403_FORBIDDEN


@dataclass(frozen=True)
class InsufficientPermissionsApplicationError(ApplicationError):
    message: str = "Insufficient permissions to perform this action."
    code: str = "INSUFFICIENT_PERMISSIONS"
    status_code: int = status.HTTP_403_FORBIDDEN


@dataclass(frozen=True)
class TokenExpiredOrRevokedApplicationError(ApplicationError):
    message: str = "Token is expired or revoked."
    code: str = "TOKEN_EXPIRED_OR_REVOKED"
    status_code: int = status.HTTP_401_UNAUTHORIZED


@dataclass(frozen=True)
class InvalidTokenTypeApplicationError(TokenExpiredOrRevokedApplicationError):
    message: str = "Invalid token type. Refresh token required."
    code: str = "INVALID_TOKEN_TYPE"


@dataclass(frozen=True)
class InvalidTokenClaimsApplicationError(TokenExpiredOrRevokedApplicationError):
    message: str = "Invalid token claims."
    code: str = "INVALID_TOKEN_CLAIMS"


@dataclass(frozen=True)
class InvalidTokenSubjectApplicationError(TokenExpiredOrRevokedApplicationError):
    message: str = "Invalid token subject."
    code: str = "INVALID_TOKEN_SUBJECT"


@dataclass(frozen=True)
class TokenExpiredApplicationError(TokenExpiredOrRevokedApplicationError):
    message: str = "Refresh token has expired."
    code: str = "TOKEN_EXPIRED"


@dataclass(frozen=True)
class UserNotFoundApplicationError(TokenExpiredOrRevokedApplicationError):
    message: str = "User account not found."
    code: str = "USER_NOT_FOUND"
