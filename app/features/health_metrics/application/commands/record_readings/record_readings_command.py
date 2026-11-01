from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.shared.actor import Actor


@dataclass(frozen=True)
class RecordReadingsCommand:
    actor: Actor
    dog_id: str
    metric: HealthMetric
    values: Sequence[tuple[float, datetime | None]]
