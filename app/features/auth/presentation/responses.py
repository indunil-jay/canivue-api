from datetime import datetime
from pydantic import BaseModel


class UserResponseData(BaseModel):
    """Shape for user profile payload."""
    id: int
    email: str
    role: str
    full_name: str | None = None
    is_active: bool
    permissions: list[str] = []
    created_at: datetime
    updated_at: datetime


class LoginResponseData(BaseModel):
    """Shape for login response payload containing tokens and user data."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponseData


class TokenPairResponseData(BaseModel):
    """Shape for rotated token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
