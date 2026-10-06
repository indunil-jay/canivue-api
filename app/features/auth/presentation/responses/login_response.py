from pydantic import BaseModel

from app.features.auth.presentation.responses.user_response import UserResponseData


class LoginResponseData(BaseModel):
    """Shape for login response payload containing tokens and user data."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponseData
