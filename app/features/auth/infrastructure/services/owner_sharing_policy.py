from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.domain.value_objects.privacy_settings import PrivacySettings
from app.features.auth.infrastructure.persistence.models.user_model import UserModel


class UserPrivacySharingPolicy:
    """Reads the "share with vet" privacy setting for the dogs module's access check."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def shares_with_vets(self, owner_id: int) -> bool:
        stored = (
            await self._session.execute(
                select(UserModel.privacy_settings).where(UserModel.id == owner_id)
            )
        ).scalar_one_or_none()
        return PrivacySettings.from_dict(stored).share_with_vet
