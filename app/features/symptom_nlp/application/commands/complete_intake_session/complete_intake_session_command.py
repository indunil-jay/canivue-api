from dataclasses import dataclass


@dataclass(frozen=True)
class CompleteIntakeSessionCommand:
    session_id: str
