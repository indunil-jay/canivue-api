from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Insurance:
    provider: str
    policy_number: str
    expiry_date: date
