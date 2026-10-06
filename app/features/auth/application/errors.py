from dataclasses import dataclass
from typing import Any

from fastapi import status


@dataclass(frozen=True)
class ApplicationError:
    """Base application layer error."""

    message: str
    code: str = "APPLICATION_ERROR"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    details: Any = None


@dataclass(frozen=True)
class InvalidInputApplicationError(ApplicationError):
    message: str = "Invalid input provided."
    code: str = "INVALID_INPUT"
    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
