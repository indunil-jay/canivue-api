from fastapi import APIRouter, Depends

from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.billing.application.commands.change_plan.change_plan_command import (
    ChangePlanCommand,
)
from app.features.billing.application.commands.change_plan.change_plan_command_handler import (
    ChangePlanCommandHandler,
)
from app.features.billing.application.queries.get_current_subscription.get_current_subscription_query import (
    GetCurrentSubscriptionQuery,
)
from app.features.billing.application.queries.get_current_subscription.get_current_subscription_query_handler import (
    GetCurrentSubscriptionQueryHandler,
)
from app.features.billing.application.queries.list_plans.list_plans_query import ListPlansQuery
from app.features.billing.application.queries.list_plans.list_plans_query_handler import (
    ListPlansQueryHandler,
)
from app.features.billing.presentation.dependencies import (
    get_change_plan_command_handler,
    get_current_subscription_query_handler,
    get_list_plans_query_handler,
)
from app.features.billing.presentation.requests.change_plan_request import ChangePlanRequest
from app.features.billing.presentation.responses.current_subscription_response import (
    CurrentSubscriptionResponse,
)
from app.features.billing.presentation.responses.subscription_plan_response import (
    SubscriptionPlanResponse,
)
from app.shared.actor import Actor

router = APIRouter()


Current = APIResponse[CurrentSubscriptionResponse]


@router.get(
    "/plans",
    response_model=APIResponse[list[SubscriptionPlanResponse]],
    summary="List subscription plans, cheapest first",
)
async def list_plans(
    actor: Actor = Depends(get_actor),
    handler: ListPlansQueryHandler = Depends(get_list_plans_query_handler),
) -> APIResponse[list[SubscriptionPlanResponse]]:
    plans = await handler.handle(ListPlansQuery())
    return APIResponse(
        message="Plans retrieved successfully",
        data=[SubscriptionPlanResponse.model_validate(p) for p in plans],
    )


@router.get(
    "/subscription", response_model=Current, summary="Get my subscription, usage and invoices"
)
async def get_current_subscription(
    actor: Actor = Depends(get_actor),
    handler: GetCurrentSubscriptionQueryHandler = Depends(get_current_subscription_query_handler),
) -> Current:
    current = await handler.handle(GetCurrentSubscriptionQuery(actor=actor))
    return APIResponse(
        message="Subscription retrieved successfully",
        data=CurrentSubscriptionResponse.model_validate(current),
    )


@router.put(
    "/subscription",
    response_model=Current,
    summary="Change my plan",
    description="Moving to a paid plan charges one month through the payment gateway and "
    "records an invoice. Usage limits are reported, not enforced.",
)
async def change_plan(
    payload: ChangePlanRequest,
    actor: Actor = Depends(get_actor),
    handler: ChangePlanCommandHandler = Depends(get_change_plan_command_handler),
) -> Current:
    current = await handler.handle(ChangePlanCommand(actor=actor, plan_id=payload.plan_id))
    return APIResponse(
        message="Plan changed successfully",
        data=CurrentSubscriptionResponse.model_validate(current),
    )
