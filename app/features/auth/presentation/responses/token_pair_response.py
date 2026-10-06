from pydantic import BaseModel


class TokenPairResponseData(BaseModel):
    """Shape for rotated token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
