from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from app.core.exceptions import ConflictException
from app.shared.entity import BaseEntity, _utc_now


class AppointmentNotCompletedError(ConflictException):
    def __init__(self) -> None:
        super().__init__(message="Only a completed appointment can be reviewed.")


class AlreadyReviewedError(ConflictException):
    def __init__(self) -> None:
        super().__init__(message="This appointment has already been reviewed.")


@dataclass
class Review(BaseEntity):
    appointment_id: str = ""
    vet_id: str = ""
    owner_id: int = 0
    owner_name: str = ""
    rating: int = 5
    comment: str = ""
    date: datetime = field(default_factory=_utc_now)


@dataclass(frozen=True)
class VetReputation:
    average_rating: float
    total_consultations: int
    recommendations_accepted_percent: int
    repeat_consultation_percent: int
    reviews: Sequence[Review]


class ReviewRepositoryProtocol(Protocol):
    async def create(self, entity: Review) -> Review: ...

    async def exists_for_appointment(self, appointment_id: str) -> bool: ...

    async def list_for_vet(self, vet_id: str) -> Sequence[Review]: ...
