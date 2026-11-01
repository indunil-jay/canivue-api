from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class DeleteMedicalRecordCommand:
    actor: Actor
    dog_id: str
    record_id: str
