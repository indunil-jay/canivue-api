from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol

from app.core.exceptions import AppException, NotFoundException
from app.shared.entity import BaseEntity, _utc_now

UNLIMITED = -1
BILLING_PERIOD = timedelta(days=30)
FREE_PLAN_ID = "free"


@dataclass(frozen=True)
class SubscriptionPlan:
    id: str
    name: str
    price_monthly: float
    features: tuple[str, ...]
    max_dogs: int
    ai_analyses_per_month: int
    max_devices: int
    vet_consultations_per_month: int


PLANS: dict[str, SubscriptionPlan] = {
    p.id: p
    for p in (
        SubscriptionPlan(
            "free", "Free", 0.0,
            ("1 dog profile", "5 AI analyses / month", "Community access"),
            max_dogs=1, ai_analyses_per_month=5, max_devices=1, vet_consultations_per_month=1,
        ),
        SubscriptionPlan(
            "premium", "Premium", 12.99,
            (
                "Up to 3 dogs", "Unlimited AI analyses", "2 smart collar devices",
                "2 vet consultations / month", "Priority support",
            ),
            max_dogs=3, ai_analyses_per_month=UNLIMITED, max_devices=2,
            vet_consultations_per_month=2,
        ),
        SubscriptionPlan(
            "pro", "Pro", 24.99,
            (
                "Unlimited dogs", "Unlimited AI analyses", "Unlimited devices",
                "Unlimited vet consultations", "Dedicated care coordinator",
            ),
            max_dogs=UNLIMITED, ai_analyses_per_month=UNLIMITED, max_devices=UNLIMITED,
            vet_consultations_per_month=UNLIMITED,
        ),
    )
}  # fmt: skip


class InvoiceStatus(str, Enum):
    PAID = "paid"
    PENDING = "pending"
    FAILED = "failed"


class PlanNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Subscription plan not found.")


class PaymentFailedError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Payment was declined. Your plan has not changed.", status_code=402
        )


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


@dataclass
class Invoice(BaseEntity):
    user_id: int = 0
    date: datetime = field(default_factory=_utc_now)
    amount: float = 0.0
    status: InvoiceStatus = InvoiceStatus.PAID
    description: str = ""


@dataclass(frozen=True)
class UsageLimit:
    label: str
    used: int
    limit: int


@dataclass(frozen=True)
class CurrentSubscription:
    plan_id: str
    renews_at: datetime | None
    usage: list[UsageLimit]
    invoices: Sequence[Invoice]


@dataclass(frozen=True)
class Usage:
    dogs: int
    ai_analyses: int
    devices: int
    vet_consultations: int


class BillingRepositoryProtocol(Protocol):
    async def get_subscription(self, user_id: int) -> Subscription | None: ...

    async def save_subscription(self, subscription: Subscription) -> Subscription: ...

    async def add_invoice(self, invoice: Invoice) -> Invoice: ...

    async def list_invoices(self, user_id: int) -> Sequence[Invoice]: ...


class UsageMeterProtocol(Protocol):
    """Counts what a user has actually used, from the modules that own the data."""

    async def measure(self, user_id: int, since: datetime) -> Usage: ...


class PaymentGatewayProtocol(Protocol):
    async def charge(self, user_id: int, amount: float, description: str) -> bool:
        """Takes payment. Returns whether it succeeded."""
        ...
