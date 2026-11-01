from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.health_metrics.application.interfaces.repositories.metric_reading_repository import (
    MetricReadingRepositoryProtocol,
)
from app.features.health_metrics.presentation.dependencies import get_metric_reading_repository
from app.features.nutrition.application.commands.update_nutrition_plan.update_nutrition_plan_command_handler import (
    UpdateNutritionPlanCommandHandler,
)
from app.features.nutrition.application.interfaces.repositories.nutrition_plan_repository import (
    NutritionPlanRepositoryProtocol,
)
from app.features.nutrition.application.queries.get_nutrition_profile.get_nutrition_profile_query_handler import (
    GetNutritionProfileQueryHandler,
)
from app.features.nutrition.application.services.nutrition_profiles import NutritionProfiles
from app.features.nutrition.infrastructure.persistence.repositories.nutrition_plan_repository import (
    SqlAlchemyNutritionPlanRepository,
)


def get_nutrition_plan_repository(
    session: AsyncSession = Depends(get_db_session),
) -> NutritionPlanRepositoryProtocol:
    return SqlAlchemyNutritionPlanRepository(session=session)


def get_nutrition_profiles(
    plans: NutritionPlanRepositoryProtocol = Depends(get_nutrition_plan_repository),
    readings: MetricReadingRepositoryProtocol = Depends(get_metric_reading_repository),
) -> NutritionProfiles:
    return NutritionProfiles(plans, readings)


def get_nutrition_profile_query_handler(
    profiles: NutritionProfiles = Depends(get_nutrition_profiles),
    access: DogAccess = Depends(get_dog_access),
) -> GetNutritionProfileQueryHandler:
    return GetNutritionProfileQueryHandler(profiles, access)


def get_update_nutrition_plan_command_handler(
    plans: NutritionPlanRepositoryProtocol = Depends(get_nutrition_plan_repository),
    profiles: NutritionProfiles = Depends(get_nutrition_profiles),
    access: DogAccess = Depends(get_dog_access),
) -> UpdateNutritionPlanCommandHandler:
    return UpdateNutritionPlanCommandHandler(plans, profiles, access)
