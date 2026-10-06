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
