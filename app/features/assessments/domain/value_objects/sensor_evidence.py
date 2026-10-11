from dataclasses import dataclass


@dataclass(frozen=True)
class SensorEvidence:
    reading_count: int
    abnormal_fraction: float
