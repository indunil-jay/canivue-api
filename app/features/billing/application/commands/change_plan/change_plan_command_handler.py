from datetime import datetime, timezone

from app.features.billing.application.commands.change_plan.change_plan_command import (
    ChangePlanCommand,
)
from app.features.billing.application.dtos.current_subscription import CurrentSubscription
from app.features.billing.application.interfaces.repositories.billing_repository import (
    BillingRepositoryProtocol,
)
from app.features.billing.application.interfaces.services.payment_gateway import (
    PaymentGatewayProtocol,
)
from app.features.billing.application.services.current_subscriptions import CurrentSubscriptions
from app.features.billing.domain.constants import PLANS
from app.features.billing.domain.entities.invoice import Invoice
from app.features.billing.domain.enums.invoice_status import InvoiceStatus
from app.features.billing.domain.exceptions import PaymentFailedError, PlanNotFoundError
from app.shared.notifier import NotificationType, NotifierProtocol


class ChangePlanCommandHandler:
    def __init__(
        self,
        billing: BillingRepositoryProtocol,
        subscriptions: CurrentSubscriptions,
        gateway: PaymentGatewayProtocol,
        notifier: NotifierProtocol,
    ):
        self._billing = billing
        self._subscriptions = subscriptions
        self._gateway = gateway
        self._notifier = notifier

    async def handle(self, command: ChangePlanCommand) -> CurrentSubscription:
        plan = PLANS.get(command.plan_id)
        if plan is None:
            raise PlanNotFoundError()
        subscription = await self._subscriptions.subscription_of(command.actor.id)
        if subscription.plan_id == plan.id:
            return await self._subscriptions.of(command.actor.id)

        now = datetime.now(timezone.utc)
        if plan.price_monthly > 0:
            description = f"Canivue {plan.name} — monthly"
            if not await self._gateway.charge(command.actor.id, plan.price_monthly, description):
                raise PaymentFailedError()
            await self._billing.add_invoice(
                Invoice(
                    user_id=command.actor.id,
                    date=now,
                    amount=plan.price_monthly,
                    status=InvoiceStatus.PAID,
                    description=description,
                )
            )

        subscription.switch_to(plan, now)
        await self._billing.save_subscription(subscription)
        await self._notifier.notify(
            command.actor.id,
            NotificationType.BILLING,
            f"You're now on the {plan.name} plan",
            (
                f"${plan.price_monthly:.2f} was charged. Your plan renews on "
                f"{subscription.renews_at:%d %b %Y}."
                if subscription.renews_at
                else "Your paid plan has ended and you will not be charged again."
            ),
            action_label="View Subscription",
        )
        return await self._subscriptions.of(command.actor.id)
