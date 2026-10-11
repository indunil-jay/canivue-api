from datetime import datetime, timezone

from app.features.billing.application.interfaces.repositories.billing_repository import (
    BillingRepositoryProtocol,
)
from app.features.billing.application.interfaces.services.usage_meter import UsageMeterProtocol
from app.features.billing.domain.entities.subscription import Subscription
from app.features.billing.domain.value_objects.current_subscription import CurrentSubscription
from app.features.billing.domain.value_objects.usage_limit import UsageLimit


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
