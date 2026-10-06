from typing import Any

from fastapi import status

from app.core.exceptions import AppException


class EmptySymptomTextException(AppException):
    def __init__(
        self, message: str = "Symptom description text cannot be empty.", details: Any | None = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class SymptomParsingFailedException(AppException):
    def __init__(self, message: str = "Failed to parse symptom text.", details: Any | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class IntakeSessionNotFoundException(AppException):
    def __init__(self, message: str = "Intake session not found.", details: Any | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class IntakeSessionClosedException(AppException):
    def __init__(
        self,
        message: str = "Intake session is already completed or diverted.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )
