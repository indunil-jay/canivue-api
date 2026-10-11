from collections import Counter, defaultdict
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Integer, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.dataclass_repository import DataclassRepository
from app.core.models import UtcDateTime, UuidTimestampMixin
from app.features.appointments.domain.entities import AppointmentStatus
from app.features.appointments.infrastructure.persistence.models import AppointmentModel
from app.features.reviews.domain.entities import Review, ReviewRepositoryProtocol
from app.features.veterinarians.domain.entities import VetStats
from app.features.veterinarians.domain.repositories import VetStatsProviderProtocol


class ReviewModel(UuidTimestampMixin, Base):
    __tablename__ = "vet_reviews"

    appointment_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    vet_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    date: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)


class SqlAlchemyReviewRepository(
    DataclassRepository[Review, ReviewModel], ReviewRepositoryProtocol
):
    _model_cls = ReviewModel
    _entity_cls = Review

    async def exists_for_appointment(self, appointment_id: str) -> bool:
        return await self.count(ReviewModel.appointment_id == appointment_id) > 0

    async def list_for_vet(self, vet_id: str) -> Sequence[Review]:
        return await self.find(ReviewModel.vet_id == vet_id, order_by=ReviewModel.date.desc())


class ReputationStatsProvider(VetStatsProviderProtocol):
    """Reputation from real rows: reviews and completed appointments.

    The share of accepted recommendations is not tracked anywhere yet, so it stays at zero.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def stats_for(self, vet_ids: Sequence[str]) -> dict[str, VetStats]:
        if not vet_ids:
            return {}
        ratings = {
            vet_id: (float(average), count)
            for vet_id, average, count in (
                await self._session.execute(
                    select(ReviewModel.vet_id, func.avg(ReviewModel.rating), func.count())
                    .where(ReviewModel.vet_id.in_(vet_ids))
                    .group_by(ReviewModel.vet_id)
                )
            ).all()
        }
        visits_by_owner: dict[str, Counter] = defaultdict(Counter)
        completed = await self._session.execute(
            select(AppointmentModel.vet_id, AppointmentModel.owner_id).where(
                AppointmentModel.vet_id.in_(vet_ids),
                AppointmentModel.status == AppointmentStatus.COMPLETED.value,
            )
        )
        for vet_id, owner_id in completed.all():
            visits_by_owner[vet_id][owner_id] += 1

        stats = {}
        for vet_id in vet_ids:
            average, review_count = ratings.get(vet_id, (0.0, 0))
            owners = visits_by_owner[vet_id]
            returning = sum(1 for visits in owners.values() if visits > 1)
            stats[vet_id] = VetStats(
                rating=round(average, 1),
                review_count=review_count,
                consultation_count=sum(owners.values()),
                follow_up_rate_percent=round(returning / len(owners) * 100) if owners else 0,
                recommendations_accepted_percent=0,
            )
        return stats
