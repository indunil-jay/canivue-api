from fastapi import APIRouter, Depends

from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.nutrition.application.commands.update_nutrition_plan.update_nutrition_plan_command import (
    UpdateNutritionPlanCommand,
)
from app.features.nutrition.application.commands.update_nutrition_plan.update_nutrition_plan_command_handler import (
    UpdateNutritionPlanCommandHandler,
)
from app.features.nutrition.application.queries.get_nutrition_profile.get_nutrition_profile_query import (
    GetNutritionProfileQuery,
)
from app.features.nutrition.application.queries.get_nutrition_profile.get_nutrition_profile_query_handler import (
    GetNutritionProfileQueryHandler,
)
from app.features.nutrition.presentation.dependencies import (
    get_nutrition_profile_query_handler,
    get_update_nutrition_plan_command_handler,
)
from app.features.nutrition.presentation.requests.update_nutrition_plan_request import (
    UpdateNutritionPlanRequest,
)
from app.features.nutrition.presentation.responses.nutrition_profile_response import (
    NutritionProfileResponse,
)
from app.shared.actor import Actor

router = APIRouter()


Profile = APIResponse[NutritionProfileResponse]


@router.get("/{dog_id}/nutrition", response_model=Profile, summary="Get a Dog's nutrition profile")
async def get_nutrition_profile(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: GetNutritionProfileQueryHandler = Depends(get_nutrition_profile_query_handler),
) -> Profile:
    profile = await handler.handle(GetNutritionProfileQuery(actor=actor, dog_id=dog_id))
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
    handler: UpdateNutritionPlanCommandHandler = Depends(get_update_nutrition_plan_command_handler),
) -> Profile:
    profile = await handler.handle(
        UpdateNutritionPlanCommand(actor=actor, dog_id=dog_id, changes=payload.to_domain())
    )
    return APIResponse(
        message="Nutrition plan updated", data=NutritionProfileResponse.model_validate(profile)
    )
