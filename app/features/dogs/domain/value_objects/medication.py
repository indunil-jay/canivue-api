from dataclasses import dataclass


@dataclass(frozen=True)
class Medication:
    name: str
    dosage: str
    frequency: str
