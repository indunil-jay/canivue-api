from pydantic import BaseModel, EmailStr, Field


class CreateStaffRequest(BaseModel):
    """Payload for staff member provisioning by admin."""

    email: EmailStr = Field(..., description="Staff member email address")
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")
    role: str = Field(..., description="Staff role: VET or ADMIN")
    full_name: str | None = Field(None, max_length=255, description="Full name of staff member")
