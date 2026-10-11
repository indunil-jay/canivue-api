from app.features.dogs.application.services.dog_access import DogAccess
from app.features.medical_records.application.commands.add_medical_record.add_medical_record_command import (
    AddMedicalRecordCommand,
)
from app.features.medical_records.application.interfaces.repositories.medical_record_repository import (
    MedicalRecordRepositoryProtocol,
)
from app.features.medical_records.domain.constants import CLINICAL_TYPES
from app.features.medical_records.domain.entities.medical_record import MedicalRecord
from app.features.medical_records.domain.exceptions import ClinicalRecordForbiddenError
from app.shared.entity import _utc_now


class AddMedicalRecordCommandHandler:
    def __init__(self, records: MedicalRecordRepositoryProtocol, access: DogAccess):
        self._records = records
        self._access = access

    async def handle(self, command: AddMedicalRecordCommand) -> MedicalRecord:
        dog = await self._access.readable(command.actor, command.dog_id)
        treating = dog.owner_id != command.actor.id and (
            command.actor.is_vet or command.actor.is_admin
        )
        if command.data.type in CLINICAL_TYPES and not treating:
            raise ClinicalRecordForbiddenError()
        return await self._records.create(
            MedicalRecord(
                dog_id=dog.id,
                type=command.data.type,
                title=command.data.title.strip(),
                description=command.data.description.strip(),
                date=command.data.date or _utc_now(),
                author_user_id=command.actor.id,
                author_name=command.actor.display_name,
                authored_by_vet=treating and command.actor.is_vet,
            )
        )
