from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.error_type import ERROR_TYPE_HTTP_STATUS_MAP, ErrorType


class AppException(Exception):
    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.FAILURE,
        status_code: int | None = None,
        details: Any | None = None,
    ):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code or ERROR_TYPE_HTTP_STATUS_MAP.get(
            error_type, status.HTTP_400_BAD_REQUEST
        )
        self.details = details
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: Any | None = None):
        super().__init__(
            message=message,
            error_type=ErrorType.NOT_FOUND,
            details=details,
        )


class ConflictException(AppException):
    def __init__(self, message: str = "Resource conflict occurred", details: Any | None = None):
        super().__init__(
            message=message,
            error_type=ErrorType.CONFLICT,
            details=details,
        )


class ValidationException(AppException):
    def __init__(self, message: str = "Validation failed", details: Any | None = None):
        super().__init__(
            message=message,
            error_type=ErrorType.VALIDATION,
            details=details,
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", details: Any | None = None):
        super().__init__(
            message=message,
            error_type=ErrorType.UNAUTHORIZED,
            details=details,
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", details: Any | None = None):
        super().__init__(
            message=message,
            error_type=ErrorType.FORBIDDEN,
            details=details,
        )


class ConcurrencyException(AppException):
    def __init__(self, message: str = "Concurrency conflict occurred", details: Any | None = None):
        super().__init__(
            message=message,
            error_type=ErrorType.CONCURRENCY,
            details=details,
        )


class ProblemException(AppException):
    def __init__(self, message: str = "An unexpected problem occurred", details: Any | None = None):
        super().__init__(
            message=message,
            error_type=ErrorType.PROBLEM,
            details=details,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "type": exc.error_type.value,
                "details": exc.details,
            },
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "message": "An unexpected error occurred.",
                "details": str(exc) if request.app.debug else None,
            },
        },
    )
