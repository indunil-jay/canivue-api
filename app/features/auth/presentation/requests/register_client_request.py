from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterClientRequest(BaseModel):
    email: EmailStr = Field(..., description="Unique user email address")
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")
    full_name: str | None = Field(None, max_length=255, description="Full name of the user")
    role: Literal["CLIENT", "VET"] = Field(
        "CLIENT", description="Dog owner (CLIENT) or veterinarian (VET)"
    )
