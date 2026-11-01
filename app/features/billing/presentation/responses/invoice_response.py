from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.features.billing.domain.enums.invoice_status import InvoiceStatus


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    date: datetime
    amount: float
    status: InvoiceStatus
    description: str
