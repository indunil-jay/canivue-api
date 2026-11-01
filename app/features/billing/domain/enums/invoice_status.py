from enum import Enum


class InvoiceStatus(str, Enum):
    PAID = "paid"
    PENDING = "pending"
    FAILED = "failed"
