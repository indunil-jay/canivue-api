from dataclasses import dataclass
from datetime import datetime

from app.features.billing.domain.enums.invoice_status import InvoiceStatus


@dataclass(frozen=True)
class InvoiceOutputDTO:
    id: str
    user_id: int
    date: datetime
    amount: float
    status: InvoiceStatus
    description: str
    created_at: datetime
    updated_at: datetime | None
