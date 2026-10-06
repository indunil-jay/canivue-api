from app.core.exceptions import AppException
from app.features.auth.application.errors import (
    AccountDisabledApplicationError,
    InsufficientPermissionsApplicationError,
    InvalidCredentialsApplicationError,
    TokenExpiredOrRevokedApplicationError,
)


class InvalidCredentialsError(AppException):
    def __init__(self, message: str = InvalidCredentialsApplicationError.message):
        err = InvalidCredentialsApplicationError(message=message)
        super().__init__(message=err.message, status_code=err.status_code)


class AccountDisabledError(AppException):
    def __init__(self, message: str = AccountDisabledApplicationError.message):
        err = AccountDisabledApplicationError(message=message)
        super().__init__(message=err.message, status_code=err.status_code)


class InsufficientPermissionsError(AppException):
    def __init__(self, message: str = InsufficientPermissionsApplicationError.message):
        err = InsufficientPermissionsApplicationError(message=message)
        super().__init__(message=err.message, status_code=err.status_code)


class TokenExpiredOrRevokedError(AppException):
    def __init__(self, message: str = TokenExpiredOrRevokedApplicationError.message):
        err = TokenExpiredOrRevokedApplicationError(message=message)
        super().__init__(message=err.message, status_code=err.status_code)
