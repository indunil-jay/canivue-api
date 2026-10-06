from dataclasses import dataclass
from datetime import datetime


@dataclass
class PasswordResetToken:
    id: int | None
    user_id: int
    token_hash: str
    expires_at: datetime
    is_used: bool = False
    created_at: datetime | None = None
