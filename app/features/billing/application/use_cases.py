from datetime import datetime, timezone

from app.features.billing.domain.entities import (
    PLANS,
    BillingRepositoryProtocol,
    CurrentSubscription,
    Invoice,
    InvoiceStatus,
    PaymentFailedError,
    PaymentGatewayProtocol,
    PlanNotFoundError,
    Subscription,
    SubscriptionPlan,
    UsageLimit,
    UsageMeterProtocol,
)
from app.shared.actor import Actor
from app.shared.notifier import NotificationType, NotifierProtocol


class ListPlansUseCase:
    async def execute(self) -> list[SubscriptionPlan]:
        return sorted(PLANS.values(), key=lambda p: p.price_monthly)


class CurrentSubscriptions:
    def __init__(self, billing: BillingRepositoryProtocol, meter: UsageMeterProtocol):
        self._billing = billing
        self._meter = meter

    async def subscription_of(self, user_id: int) -> Subscription:
        """A user who never subscribed is on the free plan, counted from the start of the month."""
        existing = await self._billing.get_subscription(user_id)
        if existing:
            return existing
        month_start = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        return Subscription(user_id=user_id, period_start=month_start)

    async def of(self, user_id: int) -> CurrentSubscription:
        subscription = await self.subscription_of(user_id)
        plan = subscription.plan
        used = await self._meter.measure(user_id, subscription.period_start)
        return CurrentSubscription(
            plan_id=plan.id,
            renews_at=subscription.renews_at,
            usage=[
                UsageLimit("Dog Profiles", used.dogs, plan.max_dogs),
                UsageLimit("AI Analyses", used.ai_analyses, plan.ai_analyses_per_month),
                UsageLimit("Connected Devices", used.devices, plan.max_devices),
                UsageLimit(
                    "Vet Consultations", used.vet_consultations, plan.vet_consultations_per_month
                ),
            ],
            invoices=await self._billing.list_invoices(user_id),
        )


class GetCurrentSubscriptionUseCase:
    def __init__(self, subscriptions: CurrentSubscriptions):
        self._subscriptions = subscriptions

    async def execute(self, actor: Actor) -> CurrentSubscription:
        return await self._subscriptions.of(actor.id)


class ChangePlanUseCase:
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

    async def execute(self, actor: Actor, plan_id: str) -> CurrentSubscription:
        plan = PLANS.get(plan_id)
        if plan is None:
            raise PlanNotFoundError()
        subscription = await self._subscriptions.subscription_of(actor.id)
        if subscription.plan_id == plan.id:
            return await self._subscriptions.of(actor.id)

        now = datetime.now(timezone.utc)
        if plan.price_monthly > 0:
            description = f"Canivue {plan.name} — monthly"
            if not await self._gateway.charge(actor.id, plan.price_monthly, description):
                raise PaymentFailedError()
            await self._billing.add_invoice(
                Invoice(
                    user_id=actor.id,
                    date=now,
                    amount=plan.price_monthly,
                    status=InvoiceStatus.PAID,
                    description=description,
                )
            )

        subscription.switch_to(plan, now)
        await self._billing.save_subscription(subscription)
        await self._notifier.notify(
            actor.id,
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
        return await self._subscriptions.of(actor.id)
