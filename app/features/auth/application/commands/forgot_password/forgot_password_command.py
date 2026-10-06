from dataclasses import dataclass


@dataclass(frozen=True)
class ForgotPasswordCommand:
    email: str
