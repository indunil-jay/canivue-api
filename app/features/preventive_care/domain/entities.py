from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol

from app.core.exceptions import NotFoundException
from app.shared.entity import BaseEntity, _utc_now


class CareTaskCategory(str, Enum):
    VACCINATION = "vaccination"
    DEWORMING = "deworming"
    FLEA_TICK = "fleaTick"
    DENTAL = "dental"
    GROOMING = "grooming"
    ANNUAL_CHECK = "annualCheck"
    WEIGHT_GOAL = "weightGoal"
    MEDICATION = "medication"


class CareTaskNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Care task not found.")


@dataclass
class CareTask(BaseEntity):
    dog_id: str = ""
    category: CareTaskCategory = CareTaskCategory.VACCINATION
    title: str = ""
    due_date: datetime = field(default_factory=_utc_now)
    completed: bool = False
    completed_at: datetime | None = None

    @property
    def is_overdue(self) -> bool:
        return not self.completed and self.due_date < _utc_now()

    def complete(self) -> None:
        if not self.completed:
            self.completed = True
            self.completed_at = _utc_now()


class CareTaskRepositoryProtocol(Protocol):
    async def get_by_id(self, entity_id: str) -> CareTask | None: ...

    async def list_for_dog(self, dog_id: str) -> Sequence[CareTask]: ...

    async def create(self, entity: CareTask) -> CareTask: ...

    async def update(self, entity: CareTask) -> CareTask: ...

    async def delete(self, entity_id: str) -> bool: ...
