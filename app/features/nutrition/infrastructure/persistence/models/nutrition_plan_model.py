from sqlalchemy import JSON, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UuidTimestampMixin


class NutritionPlanModel(UuidTimestampMixin, Base):
    __tablename__ = "nutrition_plans"

    dog_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    weight_goal_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    daily_calorie_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_condition_score: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    nutrition_goal: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    feeding_schedule: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
