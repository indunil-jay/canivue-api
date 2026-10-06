from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Payload for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
