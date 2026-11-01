from collections.abc import Sequence

from app.core.dataclass_repository import DataclassRepository
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.domain.entities.vet_profile import VetProfile
from app.features.veterinarians.infrastructure.persistence.models.vet_profile_model import (
    VetProfileModel,
)


class SqlAlchemyVetProfileRepository(
    DataclassRepository[VetProfile, VetProfileModel], VetProfileRepositoryProtocol
):
    _model_cls = VetProfileModel
    _entity_cls = VetProfile

    async def get_by_user_id(self, user_id: int) -> VetProfile | None:
        return await self.find_one(VetProfileModel.user_id == user_id)

    async def list_by_verified(self, verified: bool) -> Sequence[VetProfile]:
        return await self.find(
            VetProfileModel.verified.is_(verified), order_by=VetProfileModel.created_at
        )
