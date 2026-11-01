from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dataclass_repository import DataclassRepository
from app.features.billing.application.interfaces.repositories.billing_repository import (
    BillingRepositoryProtocol,
)
from app.features.billing.domain.entities.invoice import Invoice
from app.features.billing.domain.entities.subscription import Subscription
from app.features.billing.infrastructure.persistence.models.invoice_model import InvoiceModel
from app.features.billing.infrastructure.persistence.models.subscription_model import (
    SubscriptionModel,
)


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
