from dataclasses import dataclass


@dataclass(frozen=True)
class VerifyEmailCommand:
    email: str
    code: str
