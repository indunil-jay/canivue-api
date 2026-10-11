from dataclasses import dataclass


@dataclass(frozen=True)
class ConductIntakeTurnCommand:
    session_id: str
    message: str
