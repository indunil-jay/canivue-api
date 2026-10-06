from pydantic import BaseModel

from app.features.auth.presentation.responses.user_response import UserResponseData


class LoginResponseData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponseData
