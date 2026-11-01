from pydantic import BaseModel, ConfigDict, Field


class FeedingScheduleEntrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: str = Field(..., pattern=r"^([01]\d|2[0-3]):[0-5]\d$", description="24-hour HH:MM")
    food_name: str = Field(..., min_length=1, max_length=100)
    portion_grams: int = Field(..., gt=0, le=5000)
