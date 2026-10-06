from app.core.exceptions import AppException, ConflictException
from app.features.auth.domain.errors import (
    AccountDisabledDomainError,
    InsufficientPermissionsDomainError,
    InvalidCredentialsDomainError,
    TokenExpiredOrRevokedDomainError,
    UserAlreadyExistsDomainError,
)


class UserAlreadyExistsError(ConflictException):
    def __init__(self, email: str):
        err = UserAlreadyExistsDomainError(message=f"User with email '{email}' already exists.")
        super().__init__(message=err.message)


class InvalidCredentialsError(AppException):
    def __init__(self, message: str = InvalidCredentialsDomainError.message):
        err = InvalidCredentialsDomainError(message=message)
        super().__init__(message=err.message, status_code=err.status_code)


class AccountDisabledError(AppException):
    def __init__(self, message: str = AccountDisabledDomainError.message):
        err = AccountDisabledDomainError(message=message)
        super().__init__(message=err.message, status_code=err.status_code)


class InsufficientPermissionsError(AppException):
    def __init__(self, message: str = InsufficientPermissionsDomainError.message):
        err = InsufficientPermissionsDomainError(message=message)
        super().__init__(message=err.message, status_code=err.status_code)


class TokenExpiredOrRevokedError(AppException):
    def __init__(self, message: str = TokenExpiredOrRevokedDomainError.message):
        err = TokenExpiredOrRevokedDomainError(message=message)
        super().__init__(message=err.message, status_code=err.status_code)
