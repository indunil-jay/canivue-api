from dataclasses import dataclass


@dataclass(frozen=True)
class ModelContribution:
    model_name: str
    contribution_percent: float
