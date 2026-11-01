from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.file_storage import get_file_storage
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.medical_records.application.commands.add_medical_record.add_medical_record_command_handler import (
    AddMedicalRecordCommandHandler,
)
from app.features.medical_records.application.commands.delete_medical_record.delete_medical_record_command_handler import (
    DeleteMedicalRecordCommandHandler,
)
from app.features.medical_records.application.commands.upload_medical_document.upload_medical_document_command_handler import (
    UploadMedicalDocumentCommandHandler,
)
from app.features.medical_records.application.interfaces.repositories.medical_record_repository import (
    MedicalRecordRepositoryProtocol,
)
from app.features.medical_records.application.queries.get_record_attachment.get_record_attachment_query_handler import (
    GetRecordAttachmentQueryHandler,
)
from app.features.medical_records.application.queries.list_medical_records.list_medical_records_query_handler import (
    ListMedicalRecordsQueryHandler,
)
from app.features.medical_records.infrastructure.persistence.repositories.medical_record_repository import (
    SqlAlchemyMedicalRecordRepository,
)
from app.shared.files import FileStorageProtocol


def get_record_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MedicalRecordRepositoryProtocol:
    return SqlAlchemyMedicalRecordRepository(session=session)


def get_list_medical_records_query_handler(
    records: MedicalRecordRepositoryProtocol = Depends(get_record_repository),
    access: DogAccess = Depends(get_dog_access),
) -> ListMedicalRecordsQueryHandler:
    return ListMedicalRecordsQueryHandler(records, access)


def get_add_medical_record_command_handler(
    records: MedicalRecordRepositoryProtocol = Depends(get_record_repository),
    access: DogAccess = Depends(get_dog_access),
) -> AddMedicalRecordCommandHandler:
    return AddMedicalRecordCommandHandler(records, access)


def get_upload_medical_document_command_handler(
    records: MedicalRecordRepositoryProtocol = Depends(get_record_repository),
    access: DogAccess = Depends(get_dog_access),
    storage: FileStorageProtocol = Depends(get_file_storage),
) -> UploadMedicalDocumentCommandHandler:
    return UploadMedicalDocumentCommandHandler(records, access, storage)


def get_record_attachment_query_handler(
    records: MedicalRecordRepositoryProtocol = Depends(get_record_repository),
    access: DogAccess = Depends(get_dog_access),
    storage: FileStorageProtocol = Depends(get_file_storage),
) -> GetRecordAttachmentQueryHandler:
    return GetRecordAttachmentQueryHandler(records, access, storage)


def get_delete_medical_record_command_handler(
    records: MedicalRecordRepositoryProtocol = Depends(get_record_repository),
    access: DogAccess = Depends(get_dog_access),
    storage: FileStorageProtocol = Depends(get_file_storage),
) -> DeleteMedicalRecordCommandHandler:
    return DeleteMedicalRecordCommandHandler(records, access, storage)
