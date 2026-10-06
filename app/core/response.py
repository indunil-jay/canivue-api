from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = Field(default=True, description="Indicates if the request was successful")
    message: str | None = Field(default=None, description="Human-readable response message")
    data: T | None = Field(default=None, description="Payload data returned by the endpoint")
