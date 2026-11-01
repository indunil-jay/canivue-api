import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.features.auth.application.interfaces.repositories.email_verification_code_repository import (
    EmailVerificationCodeRepository,
)
from app.features.auth.application.interfaces.services.email_service import EmailService
from app.features.auth.domain.entities.email_verification_code import EmailVerificationCode
from app.features.auth.domain.entities.user import User

CODE_TTL = timedelta(minutes=10)


def hash_verification_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


class EmailVerificationIssuer:
    def __init__(self, code_repo: EmailVerificationCodeRepository, email_service: EmailService):
        self._code_repo = code_repo
        self._email_service = email_service

    async def issue(self, user: User) -> None:
        code = f"{secrets.randbelow(1_000_000):06d}"
        await self._code_repo.invalidate_all_for_user(user.id)
        await self._code_repo.create(
            EmailVerificationCode(
                id=None,
                user_id=user.id,
                code_hash=hash_verification_code(code),
                expires_at=datetime.now(timezone.utc) + CODE_TTL,
            )
        )
        await self._email_service.send_verification_code_email(user.email, code)
