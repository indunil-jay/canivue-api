from dataclasses import dataclass, field
from datetime import datetime

from app.features.auth.domain.enums.role import Role
from app.features.auth.domain.value_objects.privacy_settings import PrivacySettings


@dataclass(frozen=True)
class UserOutputDTO:
    id: int
    email: str
    role: Role
    full_name: str | None
    is_active: bool
    permissions: list[str]
    created_at: datetime
    updated_at: datetime
    is_email_verified: bool = True
    phone: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    privacy: PrivacySettings = field(default_factory=PrivacySettings)
