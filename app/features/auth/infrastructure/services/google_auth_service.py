from app.features.auth.application.dtos.google_profile_dto import GoogleProfileDTO
from app.features.auth.application.exceptions import GoogleAuthFailedError
from app.features.auth.application.interfaces.services.google_auth_service import (
    GoogleAuthService,
)


class StubGoogleAuthService(GoogleAuthService):
    def __init__(self, profiles: dict[str, GoogleProfileDTO] | None = None):
        self._profiles = profiles or {}

    def register_token(self, id_token: str, profile: GoogleProfileDTO) -> None:
        self._profiles[id_token] = profile

    async def verify_id_token(self, id_token: str) -> GoogleProfileDTO:
        if id_token in self._profiles:
            profile = self._profiles[id_token]
            if not profile.email_verified:
                raise GoogleAuthFailedError("Google email is not verified.")
            return profile

        if id_token.startswith("valid_google_token_"):
            email = id_token.replace("valid_google_token_", "") + "@gmail.com"
            return GoogleProfileDTO(
                google_id=f"google_{id_token}",
                email=email,
                email_verified=True,
                full_name="Google User",
            )

        raise GoogleAuthFailedError("Invalid Google ID token.")
