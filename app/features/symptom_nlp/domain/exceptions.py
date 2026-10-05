from typing import Any

from fastapi import status

from app.core.exceptions import AppException


class EmptySymptomTextException(AppException):
    """Raised when the submitted symptom description is empty or whitespace only."""

    def __init__(self, message: str = "Symptom description text cannot be empty.", details: Any | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class SymptomParsingFailedException(AppException):
    """Raised when an internal error occurs during NLP inference."""

    def __init__(self, message: str = "Failed to parse symptom text.", details: Any | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )
