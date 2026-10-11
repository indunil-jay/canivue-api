from dataclasses import dataclass


@dataclass
class IntakeMessage:
    role: str
    content: str
    created_at: str
