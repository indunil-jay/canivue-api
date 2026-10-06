from dataclasses import dataclass

from app.features.auth.application.dtos.user_output_dto import UserOutputDTO


@dataclass(frozen=True)
class LoginResultDTO:
    access_token: str
    refresh_token: str
    token_type: str
    user: UserOutputDTO
