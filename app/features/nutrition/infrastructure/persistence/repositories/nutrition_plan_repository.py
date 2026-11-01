from dataclasses import asdict
from typing import Any

from app.core.dataclass_repository import DataclassRepository
from app.features.nutrition.application.interfaces.repositories.nutrition_plan_repository import (
    NutritionPlanRepositoryProtocol,
)
from app.features.nutrition.domain.entities.nutrition_plan import NutritionPlan
from app.features.nutrition.domain.value_objects.feeding_schedule_entry import FeedingScheduleEntry
from app.features.nutrition.infrastructure.persistence.models.nutrition_plan_model import (
    NutritionPlanModel,
)


class SqlAlchemyNutritionPlanRepository(
    DataclassRepository[NutritionPlan, NutritionPlanModel], NutritionPlanRepositoryProtocol
):
    _model_cls = NutritionPlanModel
    _entity_cls = NutritionPlan

    def _to_entity(self, model: NutritionPlanModel) -> NutritionPlan:
        plan = super()._to_entity(model)
        plan.feeding_schedule = [FeedingScheduleEntry(**e) for e in model.feeding_schedule]
        return plan

    def _to_model_dict(self, entity: NutritionPlan) -> dict[str, Any]:
        data = super()._to_model_dict(entity)
        data["feeding_schedule"] = [asdict(e) for e in entity.feeding_schedule]
        return data

    async def get_for_dog(self, dog_id: str) -> NutritionPlan | None:
        return await self.find_one(NutritionPlanModel.dog_id == dog_id)

    async def save(self, plan: NutritionPlan) -> NutritionPlan:
        if await self.get_by_id(plan.id) is None:
            return await self.create(plan)
        return await self.update(plan)
