from datetime import datetime

from pydantic import BaseModel


class UserResponseData(BaseModel):
    id: int
    email: str
    role: str
    full_name: str | None = None
    is_active: bool
    is_email_verified: bool = True
    phone: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    permissions: list[str] = []
    created_at: datetime
    updated_at: datetime
