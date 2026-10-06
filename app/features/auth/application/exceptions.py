from app.core.exceptions import AppException
from app.features.auth.application.errors import (
    AccountDisabledApplicationError,
    InsufficientPermissionsApplicationError,
    InvalidCredentialsApplicationError,
    InvalidTokenClaimsApplicationError,
    InvalidTokenSubjectApplicationError,
    InvalidTokenTypeApplicationError,
    TokenExpiredApplicationError,
    TokenExpiredOrRevokedApplicationError,
    UserNotFoundApplicationError,
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


class InvalidTokenTypeError(TokenExpiredOrRevokedError):
    def __init__(self, message: str = InvalidTokenTypeApplicationError.message):
        err = InvalidTokenTypeApplicationError(message=message)
        super().__init__(message=err.message)


class InvalidTokenClaimsError(TokenExpiredOrRevokedError):
    def __init__(self, message: str = InvalidTokenClaimsApplicationError.message):
        err = InvalidTokenClaimsApplicationError(message=message)
        super().__init__(message=err.message)


class InvalidTokenSubjectError(TokenExpiredOrRevokedError):
    def __init__(self, message: str = InvalidTokenSubjectApplicationError.message):
        err = InvalidTokenSubjectApplicationError(message=message)
        super().__init__(message=err.message)


class TokenExpiredError(TokenExpiredOrRevokedError):
    def __init__(self, message: str = TokenExpiredApplicationError.message):
        err = TokenExpiredApplicationError(message=message)
        super().__init__(message=err.message)


class UserNotFoundError(TokenExpiredOrRevokedError):
    def __init__(self, message: str = UserNotFoundApplicationError.message):
        err = UserNotFoundApplicationError(message=message)
        super().__init__(message=err.message)
