from dataclasses import dataclass, field
from datetime import datetime

from app.features.billing.domain.constants import BILLING_PERIOD, FREE_PLAN_ID, PLANS
from app.features.billing.domain.value_objects.subscription_plan import SubscriptionPlan
from app.shared.entity import BaseEntity, _utc_now


@dataclass
class Subscription(BaseEntity):
    user_id: int = 0
    plan_id: str = FREE_PLAN_ID
    period_start: datetime = field(default_factory=_utc_now)
    renews_at: datetime | None = None

    @property
    def plan(self) -> SubscriptionPlan:
        return PLANS.get(self.plan_id, PLANS[FREE_PLAN_ID])

    def switch_to(self, plan: SubscriptionPlan, now: datetime) -> None:
        self.plan_id = plan.id
        self.period_start = now
        self.renews_at = now + BILLING_PERIOD if plan.price_monthly > 0 else None
        self.updated_at = now
