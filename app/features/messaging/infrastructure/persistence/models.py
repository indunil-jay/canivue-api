from datetime import datetime

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UtcDateTime, UuidTimestampMixin


class ConversationModel(UuidTimestampMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("owner_id", "vet_id", name="uq_conversation_pair"),)

    owner_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    vet_id: Mapped[str] = mapped_column(String(36), nullable=False)
    vet_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    vet_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    last_message_preview: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    last_message_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)


class MessageModel(UuidTimestampMixin, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(10), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(15), nullable=False)
