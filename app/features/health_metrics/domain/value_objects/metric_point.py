from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MetricPoint:
    date: datetime
    value: float
    is_abnormal: bool = False
