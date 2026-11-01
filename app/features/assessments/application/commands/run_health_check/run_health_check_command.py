from dataclasses import dataclass

from app.features.assessments.application.dtos.health_check_input import HealthCheckInput
from app.shared.actor import Actor


@dataclass(frozen=True)
class RunHealthCheckCommand:
    actor: Actor
    data: HealthCheckInput
