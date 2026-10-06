from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RolePermissionModel(Base):
    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    permission_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
