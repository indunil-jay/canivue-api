from collections.abc import Sequence
from typing import Protocol

from app.features.billing.domain.entities.invoice import Invoice
from app.features.billing.domain.entities.subscription import Subscription


class BillingRepositoryProtocol(Protocol):
    async def get_subscription(self, user_id: int) -> Subscription | None: ...

    async def save_subscription(self, subscription: Subscription) -> Subscription: ...

    async def add_invoice(self, invoice: Invoice) -> Invoice: ...

    async def list_invoices(self, user_id: int) -> Sequence[Invoice]: ...
