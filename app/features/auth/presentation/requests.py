from pydantic import BaseModel, EmailStr, Field


class RegisterClientRequest(BaseModel):
    """Payload for client self-registration."""
    email: EmailStr = Field(..., description="Unique user email address")
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")
    full_name: str | None = Field(None, max_length=255, description="Full name of the user")


class CreateStaffRequest(BaseModel):
    """Payload for staff member provisioning by admin."""
    email: EmailStr = Field(..., description="Staff member email address")
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")
    role: str = Field(..., description="Staff role: VET or ADMIN")
    full_name: str | None = Field(None, max_length=255, description="Full name of staff member")


class LoginRequest(BaseModel):
    """Payload for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class RefreshTokenRequest(BaseModel):
    """Payload for refreshing JWT token pair."""
    refresh_token: str = Field(..., description="Valid refresh token")
