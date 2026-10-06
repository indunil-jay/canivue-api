from app.core.exceptions import AppException, ConflictException


class UserAlreadyExistsError(ConflictException):
    def __init__(self, email: str):
        super().__init__(f"User with email '{email}' already exists.")


class InvalidCredentialsError(AppException):
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message=message, status_code=401)


class AccountDisabledError(AppException):
    def __init__(self, message: str = "Account is disabled"):
        super().__init__(message=message, status_code=403)


class InsufficientPermissionsError(AppException):
    def __init__(self, message: str = "Insufficient permissions to perform this action"):
        super().__init__(message=message, status_code=403)


class TokenExpiredOrRevokedError(AppException):
    def __init__(self, message: str = "Token is expired or revoked"):
        super().__init__(message=message, status_code=401)
