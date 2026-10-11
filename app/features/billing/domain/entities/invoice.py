from dataclasses import dataclass, field
from datetime import datetime

from app.features.billing.domain.enums.invoice_status import InvoiceStatus
from app.shared.entity import BaseEntity, _utc_now


@dataclass
class Invoice(BaseEntity):
    user_id: int = 0
    date: datetime = field(default_factory=_utc_now)
    amount: float = 0.0
    status: InvoiceStatus = InvoiceStatus.PAID
    description: str = ""
