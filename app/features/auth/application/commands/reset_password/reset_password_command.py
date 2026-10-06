from dataclasses import dataclass


@dataclass(frozen=True)
class ResetPasswordCommand:
    token: str
    new_password: str
