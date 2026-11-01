from app.features.assessments.domain.enums.prediction_status import PredictionStatus
from app.features.health_metrics.domain.enums.health_metric import HealthMetric

VITALS = (
    HealthMetric.HEART_RATE,
    HealthMetric.TEMPERATURE,
    HealthMetric.ACTIVITY,
    HealthMetric.SLEEP,
)


ELEVATED_STATUSES = {PredictionStatus.HIGH_RISK, PredictionStatus.VET_REVIEW_RECOMMENDED}
