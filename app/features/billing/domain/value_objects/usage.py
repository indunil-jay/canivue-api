from dataclasses import dataclass


@dataclass(frozen=True)
class Usage:
    dogs: int
    ai_analyses: int
    devices: int
    vet_consultations: int
