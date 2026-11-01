from dataclasses import dataclass


@dataclass
class DurationEntity:
    value: int
    unit: str
