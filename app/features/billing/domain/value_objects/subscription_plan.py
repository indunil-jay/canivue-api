from dataclasses import dataclass


@dataclass(frozen=True)
class SubscriptionPlan:
    id: str
    name: str
    price_monthly: float
    features: tuple[str, ...]
    max_dogs: int
    ai_analyses_per_month: int
    max_devices: int
    vet_consultations_per_month: int
