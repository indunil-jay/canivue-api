from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standardized JSON envelope response for API endpoints."""

    success: bool = Field(default=True, description="Indicates if the request was successful")
    message: Optional[str] = Field(default=None, description="Human-readable response message")
    data: Optional[T] = Field(default=None, description="Payload data returned by the endpoint")
