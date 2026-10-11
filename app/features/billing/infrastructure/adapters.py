from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Float, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.dataclass_repository import DataclassRepository
from app.core.models import UtcDateTime, UuidTimestampMixin
from app.features.appointments.domain.entities import AppointmentStatus
from app.features.appointments.domain.repositories import AppointmentRepositoryProtocol
from app.features.assessments.domain.entities import PredictionRepositoryProtocol
from app.features.billing.domain.entities import (
    BillingRepositoryProtocol,
    Invoice,
    PaymentGatewayProtocol,
    Subscription,
    Usage,
    UsageMeterProtocol,
)
from app.features.devices.domain.entities import SmartCollarRepositoryProtocol
from app.features.dogs.domain.repositories import DogRepositoryProtocol


class SubscriptionModel(UuidTimestampMixin, Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    plan_id: Mapped[str] = mapped_column(String(30), nullable=False)
    period_start: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    renews_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)


class InvoiceModel(UuidTimestampMixin, Base):
    __tablename__ = "invoices"

    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")


class _Subscriptions(DataclassRepository[Subscription, SubscriptionModel]):
    _model_cls = SubscriptionModel
    _entity_cls = Subscription


class _Invoices(DataclassRepository[Invoice, InvoiceModel]):
    _model_cls = InvoiceModel
    _entity_cls = Invoice


class SqlAlchemyBillingRepository(BillingRepositoryProtocol):
    def __init__(self, session: AsyncSession):
        self._subscriptions = _Subscriptions(session)
        self._invoices = _Invoices(session)

    async def get_subscription(self, user_id: int) -> Subscription | None:
        return await self._subscriptions.find_one(SubscriptionModel.user_id == user_id)

    async def save_subscription(self, subscription: Subscription) -> Subscription:
        if await self._subscriptions.get_by_id(subscription.id) is None:
            return await self._subscriptions.create(subscription)
        return await self._subscriptions.update(subscription)

    async def add_invoice(self, invoice: Invoice) -> Invoice:
        return await self._invoices.create(invoice)

    async def list_invoices(self, user_id: int) -> Sequence[Invoice]:
        return await self._invoices.find(
            InvoiceModel.user_id == user_id, order_by=InvoiceModel.date.desc()
        )


class CrossModuleUsageMeter(UsageMeterProtocol):
    def __init__(
        self,
        dogs: DogRepositoryProtocol,
        predictions: PredictionRepositoryProtocol,
        collars: SmartCollarRepositoryProtocol,
        appointments: AppointmentRepositoryProtocol,
    ):
        self._dogs = dogs
        self._predictions = predictions
        self._collars = collars
        self._appointments = appointments

    async def measure(self, user_id: int, since: datetime) -> Usage:
        dog_ids = [d.id for d in await self._dogs.list_for_owner(user_id)]
        paired = 0
        for dog_id in dog_ids:
            collar = await self._collars.get_for_dog(dog_id)
            paired += bool(collar and collar.is_paired)
        consultations = [
            a
            for a in await self._appointments.list_for_owner(user_id)
            if a.status == AppointmentStatus.COMPLETED and a.date_time >= since
        ]
        return Usage(
            dogs=len(dog_ids),
            ai_analyses=await self._predictions.count_since(dog_ids, since),
            devices=paired,
            vet_consultations=len(consultations),
        )


class StubPaymentGateway(PaymentGatewayProtocol):
    """Stands in for a payment provider: every charge succeeds and no money moves."""

    async def charge(self, user_id: int, amount: float, description: str) -> bool:
        return True
