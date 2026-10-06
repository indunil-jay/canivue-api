from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleProfileDTO:
    google_id: str
    email: str
    email_verified: bool
    full_name: str | None = None
