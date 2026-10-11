from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.response import APIResponse
from app.features.appointments.domain.repositories import AppointmentRepositoryProtocol
from app.features.appointments.presentation.dependencies import get_appointment_repository
from app.features.assessments.domain.entities import PredictionRepositoryProtocol
from app.features.assessments.presentation.dependencies import get_prediction_repository
from app.features.auth.presentation.dependencies import get_actor
from app.features.billing.application.use_cases import (
    ChangePlanUseCase,
    CurrentSubscriptions,
    GetCurrentSubscriptionUseCase,
    ListPlansUseCase,
)
from app.features.billing.domain.entities import (
    BillingRepositoryProtocol,
    InvoiceStatus,
    PaymentGatewayProtocol,
    UsageMeterProtocol,
)
from app.features.billing.infrastructure.adapters import (
    CrossModuleUsageMeter,
    SqlAlchemyBillingRepository,
    StubPaymentGateway,
)
from app.features.devices.domain.entities import SmartCollarRepositoryProtocol
from app.features.devices.presentation.router import get_collar_repository
from app.features.dogs.domain.repositories import DogRepositoryProtocol
from app.features.dogs.presentation.dependencies import get_dog_repository
from app.features.notifications.presentation.dependencies import get_notifier
from app.shared.actor import Actor
from app.shared.notifier import NotifierProtocol

router = APIRouter()

_FROM = ConfigDict(from_attributes=True)


class SubscriptionPlanResponse(BaseModel):
    model_config = _FROM

    id: str
    name: str
    price_monthly: float
    features: list[str]


class UsageLimitResponse(BaseModel):
    model_config = _FROM

    label: str
    used: int
    limit: int = Field(..., description="-1 means unlimited")


class InvoiceResponse(BaseModel):
    model_config = _FROM

    id: str
    date: datetime
    amount: float
    status: InvoiceStatus
    description: str


class CurrentSubscriptionResponse(BaseModel):
    model_config = _FROM

    plan_id: str
    renews_at: datetime | None = Field(..., description="Null on the free plan")
    usage: list[UsageLimitResponse]
    invoices: list[InvoiceResponse]


class ChangePlanRequest(BaseModel):
    plan_id: str


Current = APIResponse[CurrentSubscriptionResponse]
_payment_gateway = StubPaymentGateway()


def get_payment_gateway() -> PaymentGatewayProtocol:
    return _payment_gateway


def get_billing_repository(
    session: AsyncSession = Depends(get_db_session),
) -> BillingRepositoryProtocol:
    return SqlAlchemyBillingRepository(session)


def get_usage_meter(
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
    collars: SmartCollarRepositoryProtocol = Depends(get_collar_repository),
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
) -> UsageMeterProtocol:
    return CrossModuleUsageMeter(dogs, predictions, collars, appointments)


def get_current_subscriptions(
    billing: BillingRepositoryProtocol = Depends(get_billing_repository),
    meter: UsageMeterProtocol = Depends(get_usage_meter),
) -> CurrentSubscriptions:
    return CurrentSubscriptions(billing, meter)


def get_current_subscription_use_case(
    subscriptions: CurrentSubscriptions = Depends(get_current_subscriptions),
) -> GetCurrentSubscriptionUseCase:
    return GetCurrentSubscriptionUseCase(subscriptions)


def get_change_plan_use_case(
    billing: BillingRepositoryProtocol = Depends(get_billing_repository),
    subscriptions: CurrentSubscriptions = Depends(get_current_subscriptions),
    gateway: PaymentGatewayProtocol = Depends(get_payment_gateway),
    notifier: NotifierProtocol = Depends(get_notifier),
) -> ChangePlanUseCase:
    return ChangePlanUseCase(billing, subscriptions, gateway, notifier)


@router.get(
    "/plans",
    response_model=APIResponse[list[SubscriptionPlanResponse]],
    summary="List subscription plans, cheapest first",
)
async def list_plans(
    actor: Actor = Depends(get_actor),
    use_case: ListPlansUseCase = Depends(ListPlansUseCase),
) -> APIResponse[list[SubscriptionPlanResponse]]:
    plans = await use_case.execute()
    return APIResponse(
        message="Plans retrieved successfully",
        data=[SubscriptionPlanResponse.model_validate(p) for p in plans],
    )


@router.get(
    "/subscription", response_model=Current, summary="Get my subscription, usage and invoices"
)
async def get_current_subscription(
    actor: Actor = Depends(get_actor),
    use_case: GetCurrentSubscriptionUseCase = Depends(get_current_subscription_use_case),
) -> Current:
    current = await use_case.execute(actor)
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
    use_case: ChangePlanUseCase = Depends(get_change_plan_use_case),
) -> Current:
    current = await use_case.execute(actor, payload.plan_id)
    return APIResponse(
        message="Plan changed successfully",
        data=CurrentSubscriptionResponse.model_validate(current),
    )
