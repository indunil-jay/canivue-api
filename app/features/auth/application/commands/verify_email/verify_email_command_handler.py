import hmac
from datetime import datetime, timezone

from app.features.auth.application.commands.verify_email.verify_email_command import (
    VerifyEmailCommand,
)
from app.features.auth.application.dtos.user_output_dto import UserOutputDTO
from app.features.auth.application.exceptions import InvalidVerificationCodeError
from app.features.auth.application.interfaces.repositories.email_verification_code_repository import (
    EmailVerificationCodeRepository,
)
from app.features.auth.application.interfaces.repositories.user_repository import UserRepository
from app.features.auth.application.mappers.user_dto_mapper import UserDTOMapper
from app.features.auth.application.services.email_verification_issuer import (
    hash_verification_code,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VerifyEmailCommandHandler:
    def __init__(self, user_repo: UserRepository, code_repo: EmailVerificationCodeRepository):
        self._user_repo = user_repo
        self._code_repo = code_repo

    async def handle(self, command: VerifyEmailCommand) -> UserOutputDTO:
        user = await self._user_repo.get_by_email(command.email.strip().lower())
        if not user or user.is_email_verified:
            raise InvalidVerificationCodeError()

        code = await self._code_repo.get_latest_for_user(user.id)
        if not code or not code.is_usable(_utc_now()):
            raise InvalidVerificationCodeError()

        if not hmac.compare_digest(code.code_hash, hash_verification_code(command.code.strip())):
            code.attempts += 1
            await self._code_repo.save(code)
            raise InvalidVerificationCodeError()

        code.is_used = True
        await self._code_repo.save(code)
        user.is_email_verified = True
        user.updated_at = _utc_now()
        return UserDTOMapper.to_output_dto(await self._user_repo.update(user))
