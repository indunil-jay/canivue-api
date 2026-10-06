from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleLoginCommand:
    id_token: str
