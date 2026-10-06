from app.core.exceptions import AppException


class InvalidCredentialsError(AppException):
    def __init__(self, message: str = "Invalid email or password.", details=None):
        super().__init__(message=message, status_code=401, details=details)


class AccountDisabledError(AppException):
    def __init__(self, message: str = "Account is disabled.", details=None):
        super().__init__(message=message, status_code=403, details=details)


class InsufficientPermissionsError(AppException):
    def __init__(self, message: str = "Insufficient permissions to perform this action.", details=None):
        super().__init__(message=message, status_code=403, details=details)


class TokenExpiredOrRevokedError(AppException):
    def __init__(self, message: str = "Token is expired or revoked.", details=None):
        super().__init__(message=message, status_code=401, details=details)


class InvalidTokenTypeError(TokenExpiredOrRevokedError):
    def __init__(self, message: str = "Invalid token type. Refresh token required.", details=None):
        super().__init__(message=message, details=details)


class InvalidTokenClaimsError(TokenExpiredOrRevokedError):
    def __init__(self, message: str = "Invalid token claims.", details=None):
        super().__init__(message=message, details=details)


class InvalidTokenSubjectError(TokenExpiredOrRevokedError):
    def __init__(self, message: str = "Invalid token subject.", details=None):
        super().__init__(message=message, details=details)


class TokenExpiredError(TokenExpiredOrRevokedError):
    def __init__(self, message: str = "Refresh token has expired.", details=None):
        super().__init__(message=message, details=details)


class UserSessionNotFoundError(TokenExpiredOrRevokedError):
    def __init__(self, message: str = "User session or account not found.", details=None):
        super().__init__(message=message, details=details)
