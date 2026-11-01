from dataclasses import dataclass


@dataclass(frozen=True)
class VerifyVeterinarianCommand:
    vet_id: str
