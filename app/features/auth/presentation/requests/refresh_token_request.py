from pydantic import BaseModel, Field


class RefreshTokenRequest(BaseModel):
    """Payload for refreshing JWT token pair."""

    refresh_token: str = Field(..., description="Valid refresh token")
