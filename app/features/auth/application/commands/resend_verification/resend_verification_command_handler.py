from app.features.auth.application.interfaces.repositories.user_repository import UserRepository
from app.features.auth.application.services.email_verification_issuer import (
    EmailVerificationIssuer,
)


class ResendVerificationCommandHandler:
    def __init__(self, user_repo: UserRepository, verification_issuer: EmailVerificationIssuer):
        self._user_repo = user_repo
        self._verification_issuer = verification_issuer

    async def handle(self, email: str) -> None:
        user = await self._user_repo.get_by_email(email.strip().lower())
        if user and user.is_active and not user.is_email_verified:
            await self._verification_issuer.issue(user)
