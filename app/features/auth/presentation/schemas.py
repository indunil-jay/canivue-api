from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterClientRequest(BaseModel):
    email: EmailStr = Field(..., description="Unique user email address")
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")
    full_name: str | None = Field(None, max_length=255, description="Full name of the user")


class UserResponseData(BaseModel):
    id: int
    email: str
    role: str
    full_name: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
