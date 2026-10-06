from app.core.exceptions import (
    ForbiddenException,
    UnauthorizedException,
)


class InvalidCredentialsError(UnauthorizedException):
    def __init__(self, message: str = "Invalid email or password.", details=None):
        super().__init__(message=message, details=details)


class AccountDisabledError(ForbiddenException):
    def __init__(self, message: str = "Account is disabled.", details=None):
        super().__init__(message=message, details=details)


class InsufficientPermissionsError(ForbiddenException):
    def __init__(
        self, message: str = "Insufficient permissions to perform this action.", details=None
    ):
        super().__init__(message=message, details=details)


class TokenExpiredOrRevokedError(UnauthorizedException):
    def __init__(self, message: str = "Token is expired or revoked.", details=None):
        super().__init__(message=message, details=details)


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


class InvalidResetTokenError(UnauthorizedException):
    def __init__(self, message: str = "Invalid or expired password reset token.", details=None):
        super().__init__(message=message, details=details)


class ResetTokenExpiredError(UnauthorizedException):
    def __init__(self, message: str = "Password reset token has expired.", details=None):
        super().__init__(message=message, details=details)


class GoogleAuthFailedError(UnauthorizedException):
    def __init__(
        self, message: str = "Google authentication failed or token is invalid.", details=None
    ):
        super().__init__(message=message, details=details)
