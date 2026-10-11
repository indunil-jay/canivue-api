from dataclasses import dataclass
from datetime import datetime

MAX_VERIFICATION_ATTEMPTS = 5


@dataclass
class EmailVerificationCode:
    id: int | None
    user_id: int
    code_hash: str
    expires_at: datetime
    is_used: bool = False
    attempts: int = 0

    def is_usable(self, now: datetime) -> bool:
        return (
            not self.is_used and self.attempts < MAX_VERIFICATION_ATTEMPTS and self.expires_at > now
        )
