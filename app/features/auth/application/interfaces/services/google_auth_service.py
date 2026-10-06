from typing import Protocol

from app.features.auth.application.dtos.google_profile_dto import GoogleProfileDTO


class GoogleAuthService(Protocol):
    async def verify_id_token(self, id_token: str) -> GoogleProfileDTO: ...
