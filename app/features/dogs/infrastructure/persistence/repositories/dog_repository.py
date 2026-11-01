from collections.abc import Sequence
from datetime import date
from typing import Any

from app.core.dataclass_repository import DataclassRepository
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.domain.entities.dog import Dog
from app.features.dogs.domain.value_objects.insurance import Insurance
from app.features.dogs.domain.value_objects.medication import Medication
from app.features.dogs.domain.value_objects.vaccination import Vaccination
from app.features.dogs.infrastructure.persistence.models.dog_model import DogModel


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


class SqlAlchemyDogRepository(DataclassRepository[Dog, DogModel], DogRepositoryProtocol):
    _model_cls = DogModel
    _entity_cls = Dog

    def _to_entity(self, model: DogModel) -> Dog:
        dog = super()._to_entity(model)
        dog.vaccinations = [
            Vaccination(v["name"], _date(v["date_given"]), _date(v.get("next_due_date")))
            for v in model.vaccinations
        ]
        dog.medications = [Medication(**m) for m in model.medications]
        dog.insurance = (
            Insurance(
                model.insurance["provider"],
                model.insurance["policy_number"],
                _date(model.insurance["expiry_date"]),
            )
            if model.insurance
            else None
        )
        return dog

    def _to_model_dict(self, entity: Dog) -> dict[str, Any]:
        data = super()._to_model_dict(entity)
        data["vaccinations"] = [
            {
                "name": v.name,
                "date_given": _iso(v.date_given),
                "next_due_date": _iso(v.next_due_date),
            }
            for v in entity.vaccinations
        ]
        data["medications"] = [
            {"name": m.name, "dosage": m.dosage, "frequency": m.frequency}
            for m in entity.medications
        ]
        data["insurance"] = (
            {
                "provider": entity.insurance.provider,
                "policy_number": entity.insurance.policy_number,
                "expiry_date": _iso(entity.insurance.expiry_date),
            }
            if entity.insurance
            else None
        )
        return data

    async def list_for_owner(self, owner_id: int) -> Sequence[Dog]:
        return await self.find(
            DogModel.owner_id == owner_id,
            DogModel.is_archived.is_(False),
            order_by=DogModel.created_at,
        )

    async def list_by_ids(self, dog_ids: Sequence[str]) -> Sequence[Dog]:
        if not dog_ids:
            return []
        return await self.find(DogModel.id.in_(dog_ids), order_by=DogModel.name)

    async def count_for_owner(self, owner_id: int) -> int:
        return await self.count(DogModel.owner_id == owner_id, DogModel.is_archived.is_(False))
