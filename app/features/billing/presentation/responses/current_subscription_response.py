from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.features.billing.presentation.responses.invoice_response import InvoiceResponse
from app.features.billing.presentation.responses.usage_limit_response import UsageLimitResponse


class CurrentSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_id: str
    renews_at: datetime | None = Field(..., description="Null on the free plan")
    usage: list[UsageLimitResponse]
    invoices: list[InvoiceResponse]
