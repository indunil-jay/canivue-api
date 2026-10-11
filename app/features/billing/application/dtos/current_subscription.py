from dataclasses import dataclass
from datetime import datetime

from app.features.billing.application.dtos.invoice_output_dto import InvoiceOutputDTO
from app.features.billing.domain.value_objects.usage_limit import UsageLimit


@dataclass(frozen=True)
class CurrentSubscription:
    plan_id: str
    renews_at: datetime | None
    usage: list[UsageLimit]
    invoices: list[InvoiceOutputDTO]
