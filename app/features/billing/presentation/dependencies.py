from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.presentation.dependencies import get_appointment_repository
from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.presentation.dependencies import get_prediction_repository
from app.features.billing.application.commands.change_plan.change_plan_command_handler import (
    ChangePlanCommandHandler,
)
from app.features.billing.application.interfaces.repositories.billing_repository import (
    BillingRepositoryProtocol,
)
from app.features.billing.application.interfaces.services.payment_gateway import (
    PaymentGatewayProtocol,
)
from app.features.billing.application.interfaces.services.usage_meter import UsageMeterProtocol
from app.features.billing.application.queries.get_current_subscription.get_current_subscription_query_handler import (
    GetCurrentSubscriptionQueryHandler,
)
from app.features.billing.application.queries.list_plans.list_plans_query_handler import (
    ListPlansQueryHandler,
)
from app.features.billing.application.services.current_subscriptions import CurrentSubscriptions
from app.features.billing.infrastructure.persistence.repositories.billing_repository import (
    SqlAlchemyBillingRepository,
)
from app.features.billing.infrastructure.services.cross_module_usage_meter import (
    CrossModuleUsageMeter,
)
from app.features.billing.infrastructure.services.stub_payment_gateway import StubPaymentGateway
from app.features.devices.application.interfaces.repositories.smart_collar_repository import (
    SmartCollarRepositoryProtocol,
)
from app.features.devices.presentation.dependencies import get_collar_repository
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.presentation.dependencies import get_dog_repository
from app.features.notifications.presentation.dependencies import get_notifier
from app.shared.notifier import NotifierProtocol

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


def get_list_plans_query_handler() -> ListPlansQueryHandler:
    return ListPlansQueryHandler()


def get_current_subscription_query_handler(
    subscriptions: CurrentSubscriptions = Depends(get_current_subscriptions),
) -> GetCurrentSubscriptionQueryHandler:
    return GetCurrentSubscriptionQueryHandler(subscriptions)


def get_change_plan_command_handler(
    billing: BillingRepositoryProtocol = Depends(get_billing_repository),
    subscriptions: CurrentSubscriptions = Depends(get_current_subscriptions),
    gateway: PaymentGatewayProtocol = Depends(get_payment_gateway),
    notifier: NotifierProtocol = Depends(get_notifier),
) -> ChangePlanCommandHandler:
    return ChangePlanCommandHandler(billing, subscriptions, gateway, notifier)
