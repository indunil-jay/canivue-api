from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.dogs.application.access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.health_metrics.domain.entities import MetricReadingRepositoryProtocol
from app.features.health_metrics.presentation.router import get_metric_reading_repository
from app.features.nutrition.application.use_cases import (
    GetNutritionProfileUseCase,
    NutritionProfiles,
    UpdateNutritionPlanUseCase,
)
from app.features.nutrition.domain.entities import (
    FeedingScheduleEntry,
    NutritionPlanRepositoryProtocol,
)
from app.features.nutrition.infrastructure.persistence.repositories import (
    SqlAlchemyNutritionPlanRepository,
)
from app.shared.actor import Actor

router = APIRouter()


class FeedingScheduleEntrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: str = Field(..., pattern=r"^([01]\d|2[0-3]):[0-5]\d$", description="24-hour HH:MM")
    food_name: str = Field(..., min_length=1, max_length=100)
    portion_grams: int = Field(..., gt=0, le=5000)


class UpdateNutritionPlanRequest(BaseModel):
    weight_goal_kg: float | None = Field(None, gt=0, le=150)
    daily_calorie_target: int | None = Field(None, gt=0, le=10_000)
    body_condition_score: int | None = Field(None, ge=1, le=9)
    nutrition_goal: str | None = Field(None, min_length=1, max_length=255)
    feeding_schedule: list[FeedingScheduleEntrySchema] | None = None

    def to_domain(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            name: getattr(self, name)
            for name in self.model_fields_set
            if getattr(self, name) is not None
        }
        if "feeding_schedule" in data:
            data["feeding_schedule"] = sorted(
                (FeedingScheduleEntry(**e.model_dump()) for e in data["feeding_schedule"]),
                key=lambda e: e.time,
            )
        return data


class NutritionProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_weight_kg: float
    weight_goal_kg: float
    thirty_day_weight_change_kg: float
    body_condition_score: int = Field(..., description="1-9; 4-5 is ideal")
    daily_calorie_target: int
    feeding_schedule: list[FeedingScheduleEntrySchema]
    nutrition_goal: str


Profile = APIResponse[NutritionProfileResponse]


def get_nutrition_plan_repository(
    session: AsyncSession = Depends(get_db_session),
) -> NutritionPlanRepositoryProtocol:
    return SqlAlchemyNutritionPlanRepository(session=session)


def get_nutrition_profiles(
    plans: NutritionPlanRepositoryProtocol = Depends(get_nutrition_plan_repository),
    readings: MetricReadingRepositoryProtocol = Depends(get_metric_reading_repository),
) -> NutritionProfiles:
    return NutritionProfiles(plans, readings)


def get_nutrition_profile_use_case(
    profiles: NutritionProfiles = Depends(get_nutrition_profiles),
    access: DogAccess = Depends(get_dog_access),
) -> GetNutritionProfileUseCase:
    return GetNutritionProfileUseCase(profiles, access)


def get_update_nutrition_plan_use_case(
    plans: NutritionPlanRepositoryProtocol = Depends(get_nutrition_plan_repository),
    profiles: NutritionProfiles = Depends(get_nutrition_profiles),
    access: DogAccess = Depends(get_dog_access),
) -> UpdateNutritionPlanUseCase:
    return UpdateNutritionPlanUseCase(plans, profiles, access)


@router.get("/{dog_id}/nutrition", response_model=Profile, summary="Get a Dog's nutrition profile")
async def get_nutrition_profile(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: GetNutritionProfileUseCase = Depends(get_nutrition_profile_use_case),
) -> Profile:
    profile = await use_case.execute(actor, dog_id)
    return APIResponse(
        message="Nutrition profile retrieved successfully",
        data=NutritionProfileResponse.model_validate(profile),
    )


@router.patch(
    "/{dog_id}/nutrition", response_model=Profile, summary="Adjust a Dog's nutrition plan"
)
async def update_nutrition_plan(
    dog_id: str,
    payload: UpdateNutritionPlanRequest,
    actor: Actor = Depends(get_actor),
    use_case: UpdateNutritionPlanUseCase = Depends(get_update_nutrition_plan_use_case),
) -> Profile:
    profile = await use_case.execute(actor, dog_id, payload.to_domain())
    return APIResponse(
        message="Nutrition plan updated", data=NutritionProfileResponse.model_validate(profile)
    )
