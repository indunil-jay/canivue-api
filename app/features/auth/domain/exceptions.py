from app.core.exceptions import AppException, ConflictException, ValidationException


class DomainValidationException(ValidationException):
    def __init__(self, message: str = "Domain validation failed.", details=None):
        super().__init__(message=message, details=details)


class InvalidEmailError(DomainValidationException):
    def __init__(self, message: str = "A valid email address is required.", details=None):
        super().__init__(message=message, details=details)


class WeakPasswordError(DomainValidationException):
    def __init__(self, message: str = "Password must be at least 8 characters long.", details=None):
        super().__init__(message=message, details=details)


class EmptyPasswordHashError(DomainValidationException):
    def __init__(self, message: str = "Hashed password must not be empty.", details=None):
        super().__init__(message=message, details=details)


class UserAlreadyExistsError(ConflictException):
    def __init__(self, email: str):
        super().__init__(message=f"User with email '{email}' already exists.")


class UserNotFoundError(AppException):
    def __init__(self, message: str = "User account not found.", details=None):
        super().__init__(message=message, status_code=404, details=details)
