from datetime import datetime

from fastapi import APIRouter, Depends, Form, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db_session
from app.core.file_storage import file_response, get_file_storage, read_upload
from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.dogs.application.access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.features.medical_records.application.use_cases import (
    AddMedicalRecordUseCase,
    DeleteMedicalRecordUseCase,
    GetRecordAttachmentUseCase,
    ListMedicalRecordsUseCase,
    NewRecordInput,
    UploadMedicalDocumentUseCase,
)
from app.features.medical_records.domain.entities import (
    MedicalRecord,
    MedicalRecordRepositoryProtocol,
    MedicalRecordType,
)
from app.features.medical_records.infrastructure.persistence.repositories import (
    SqlAlchemyMedicalRecordRepository,
)
from app.shared.actor import Actor
from app.shared.files import FileStorageProtocol

router = APIRouter()


class AddRecordRequest(BaseModel):
    type: MedicalRecordType
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field("", max_length=8000)
    date: datetime | None = None


class MedicalRecordResponse(BaseModel):
    id: str
    dog_id: str
    type: MedicalRecordType
    title: str
    description: str
    date: datetime
    attachment_url: str | None
    author_name: str
    authored_by_vet: bool

    @classmethod
    def of(cls, record: MedicalRecord) -> "MedicalRecordResponse":
        return cls(
            id=record.id,
            dog_id=record.dog_id,
            type=record.type,
            title=record.title,
            description=record.description,
            date=record.date,
            attachment_url=(
                f"/api/v1/dogs/{record.dog_id}/records/{record.id}/attachment"
                if record.file_id
                else None
            ),
            author_name=record.author_name,
            authored_by_vet=record.authored_by_vet,
        )


One = APIResponse[MedicalRecordResponse]


def get_record_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MedicalRecordRepositoryProtocol:
    return SqlAlchemyMedicalRecordRepository(session=session)


def get_list_records_use_case(
    records: MedicalRecordRepositoryProtocol = Depends(get_record_repository),
    access: DogAccess = Depends(get_dog_access),
) -> ListMedicalRecordsUseCase:
    return ListMedicalRecordsUseCase(records, access)


def get_add_record_use_case(
    records: MedicalRecordRepositoryProtocol = Depends(get_record_repository),
    access: DogAccess = Depends(get_dog_access),
) -> AddMedicalRecordUseCase:
    return AddMedicalRecordUseCase(records, access)


def get_upload_document_use_case(
    records: MedicalRecordRepositoryProtocol = Depends(get_record_repository),
    access: DogAccess = Depends(get_dog_access),
    storage: FileStorageProtocol = Depends(get_file_storage),
) -> UploadMedicalDocumentUseCase:
    return UploadMedicalDocumentUseCase(records, access, storage)


def get_record_attachment_use_case(
    records: MedicalRecordRepositoryProtocol = Depends(get_record_repository),
    access: DogAccess = Depends(get_dog_access),
    storage: FileStorageProtocol = Depends(get_file_storage),
) -> GetRecordAttachmentUseCase:
    return GetRecordAttachmentUseCase(records, access, storage)


def get_delete_record_use_case(
    records: MedicalRecordRepositoryProtocol = Depends(get_record_repository),
    access: DogAccess = Depends(get_dog_access),
    storage: FileStorageProtocol = Depends(get_file_storage),
) -> DeleteMedicalRecordUseCase:
    return DeleteMedicalRecordUseCase(records, access, storage)


@router.get(
    "/{dog_id}/records",
    response_model=APIResponse[list[MedicalRecordResponse]],
    summary="List a Dog's medical records, newest first",
)
async def list_records(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: ListMedicalRecordsUseCase = Depends(get_list_records_use_case),
) -> APIResponse[list[MedicalRecordResponse]]:
    records = await use_case.execute(actor, dog_id)
    return APIResponse(
        message="Medical records retrieved successfully",
        data=[MedicalRecordResponse.of(r) for r in records],
    )


@router.post(
    "/{dog_id}/records",
    response_model=One,
    status_code=status.HTTP_201_CREATED,
    summary="Add a medical record",
    description="Owners may add notes. A diagnosis, prescription or lab result needs a "
    "treating veterinarian. Documents are added through the upload endpoint.",
)
async def add_record(
    dog_id: str,
    payload: AddRecordRequest,
    actor: Actor = Depends(get_actor),
    use_case: AddMedicalRecordUseCase = Depends(get_add_record_use_case),
) -> One:
    record = await use_case.execute(actor, dog_id, NewRecordInput(**payload.model_dump()))
    return APIResponse(message="Medical record added", data=MedicalRecordResponse.of(record))


@router.post(
    "/{dog_id}/records/documents",
    response_model=One,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document or image as a medical record",
)
async def upload_document(
    dog_id: str,
    file: UploadFile,
    title: str = Form(..., min_length=1, max_length=255),
    actor: Actor = Depends(get_actor),
    use_case: UploadMedicalDocumentUseCase = Depends(get_upload_document_use_case),
) -> One:
    record = await use_case.execute(
        actor, dog_id, title, await read_upload(file), file.content_type, settings.MAX_UPLOAD_BYTES
    )
    return APIResponse(message="Document uploaded", data=MedicalRecordResponse.of(record))


@router.get(
    "/{dog_id}/records/{record_id}/attachment",
    response_class=Response,
    summary="Download a record's attachment",
)
async def get_attachment(
    dog_id: str,
    record_id: str,
    actor: Actor = Depends(get_actor),
    use_case: GetRecordAttachmentUseCase = Depends(get_record_attachment_use_case),
) -> Response:
    return file_response(await use_case.execute(actor, dog_id, record_id))


@router.delete(
    "/{dog_id}/records/{record_id}",
    response_model=APIResponse[None],
    summary="Delete a medical record I authored",
)
async def delete_record(
    dog_id: str,
    record_id: str,
    actor: Actor = Depends(get_actor),
    use_case: DeleteMedicalRecordUseCase = Depends(get_delete_record_use_case),
) -> APIResponse[None]:
    await use_case.execute(actor, dog_id, record_id)
    return APIResponse(message="Medical record deleted", data=None)
