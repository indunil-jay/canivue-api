from collections.abc import Sequence

from app.core.dataclass_repository import DataclassRepository
from app.features.reviews.application.interfaces.repositories.review_repository import (
    ReviewRepositoryProtocol,
)
from app.features.reviews.domain.entities.review import Review
from app.features.reviews.infrastructure.persistence.models.review_model import ReviewModel


class SqlAlchemyReviewRepository(
    DataclassRepository[Review, ReviewModel], ReviewRepositoryProtocol
):
    _model_cls = ReviewModel
    _entity_cls = Review

    async def exists_for_appointment(self, appointment_id: str) -> bool:
        return await self.count(ReviewModel.appointment_id == appointment_id) > 0

    async def list_for_vet(self, vet_id: str) -> Sequence[Review]:
        return await self.find(ReviewModel.vet_id == vet_id, order_by=ReviewModel.date.desc())
