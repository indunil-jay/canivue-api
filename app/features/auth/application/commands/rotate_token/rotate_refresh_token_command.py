from dataclasses import dataclass


@dataclass(frozen=True)
class RotateRefreshTokenCommand:
    refresh_token: str
