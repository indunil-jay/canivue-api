from dataclasses import asdict
from typing import Any

from sqlalchemy import JSON, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.dataclass_repository import DataclassRepository
from app.core.models import UuidTimestampMixin
from app.features.nutrition.domain.entities import (
    FeedingScheduleEntry,
    NutritionPlan,
    NutritionPlanRepositoryProtocol,
)


class NutritionPlanModel(UuidTimestampMixin, Base):
    __tablename__ = "nutrition_plans"

    dog_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    weight_goal_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    daily_calorie_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_condition_score: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    nutrition_goal: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    feeding_schedule: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


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
