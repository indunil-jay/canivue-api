from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.application.interfaces.repositories.email_verification_code_repository import (
    EmailVerificationCodeRepository,
)
from app.features.auth.domain.entities.email_verification_code import EmailVerificationCode
from app.features.auth.infrastructure.persistence.models.email_verification_code_model import (
    EmailVerificationCodeModel,
)


class SqlAlchemyEmailVerificationCodeRepository(EmailVerificationCodeRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, code: EmailVerificationCode) -> EmailVerificationCode:
        model = EmailVerificationCodeModel(
            user_id=code.user_id, code_hash=code.code_hash, expires_at=code.expires_at
        )
        self._session.add(model)
        await self._session.flush()
        code.id = model.id
        return code

    async def get_latest_for_user(self, user_id: int) -> EmailVerificationCode | None:
        stmt = (
            select(EmailVerificationCodeModel)
            .where(EmailVerificationCodeModel.user_id == user_id)
            .order_by(EmailVerificationCodeModel.id.desc())
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        return EmailVerificationCode(
            id=model.id,
            user_id=model.user_id,
            code_hash=model.code_hash,
            expires_at=model.expires_at,
            is_used=model.is_used,
            attempts=model.attempts,
        )

    async def save(self, code: EmailVerificationCode) -> None:
        await self._session.execute(
            update(EmailVerificationCodeModel)
            .where(EmailVerificationCodeModel.id == code.id)
            .values(is_used=code.is_used, attempts=code.attempts)
        )
        await self._session.flush()

    async def invalidate_all_for_user(self, user_id: int) -> None:
        await self._session.execute(
            update(EmailVerificationCodeModel)
            .where(EmailVerificationCodeModel.user_id == user_id)
            .values(is_used=True)
        )
        await self._session.flush()
