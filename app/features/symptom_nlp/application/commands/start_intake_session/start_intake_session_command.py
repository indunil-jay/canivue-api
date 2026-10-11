from dataclasses import dataclass


@dataclass(frozen=True)
class StartIntakeSessionCommand:
    dog_id: str
    initial_text: str
