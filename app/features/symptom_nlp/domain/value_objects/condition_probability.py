from dataclasses import dataclass


@dataclass
class ConditionProbability:
    condition: str
    probability: float
