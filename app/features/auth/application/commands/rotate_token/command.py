from dataclasses import dataclass


@dataclass(frozen=True)
class RotateRefreshTokenCommand:
    """Command payload for rotating an active refresh token."""

    refresh_token: str
