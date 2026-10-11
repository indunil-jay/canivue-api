from dataclasses import dataclass

from app.features.medical_records.application.dtos.new_record_input import NewRecordInput
from app.shared.actor import Actor


@dataclass(frozen=True)
class AddMedicalRecordCommand:
    actor: Actor
    dog_id: str
    data: NewRecordInput
