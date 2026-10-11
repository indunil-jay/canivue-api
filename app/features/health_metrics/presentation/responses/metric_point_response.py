from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MetricPointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: datetime
    value: float
    is_abnormal: bool
