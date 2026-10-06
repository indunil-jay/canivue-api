from dataclasses import dataclass


@dataclass(frozen=True)
class LoginUserCommand:
    email: str
    password: str
