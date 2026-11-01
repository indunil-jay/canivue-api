from collections import Counter, defaultdict
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.appointments.infrastructure.persistence.models.appointment_model import (
    AppointmentModel,
)
from app.features.reviews.infrastructure.persistence.models.review_model import ReviewModel
from app.features.veterinarians.application.interfaces.services.vet_stats_provider import (
    VetStatsProviderProtocol,
)
from app.features.veterinarians.domain.value_objects.vet_stats import VetStats


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
