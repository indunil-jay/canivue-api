from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UuidTimestampMixin


class CommunityPostModel(UuidTimestampMixin, Base):
    __tablename__ = "community_posts"

    author_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_veterinarian: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    community_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    community_tag: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    share_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
