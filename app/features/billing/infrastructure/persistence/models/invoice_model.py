from datetime import datetime

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UtcDateTime, UuidTimestampMixin


class InvoiceModel(UuidTimestampMixin, Base):
    __tablename__ = "invoices"

    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")
