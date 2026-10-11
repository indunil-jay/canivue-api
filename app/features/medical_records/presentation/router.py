from fastapi import APIRouter, Depends, Form, UploadFile, status
from fastapi.responses import Response

from app.config import settings
from app.core.file_storage import file_response, read_upload
from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.medical_records.application.commands.add_medical_record.add_medical_record_command import (
    AddMedicalRecordCommand,
)
from app.features.medical_records.application.commands.add_medical_record.add_medical_record_command_handler import (
    AddMedicalRecordCommandHandler,
)
from app.features.medical_records.application.commands.delete_medical_record.delete_medical_record_command import (
    DeleteMedicalRecordCommand,
)
from app.features.medical_records.application.commands.delete_medical_record.delete_medical_record_command_handler import (
    DeleteMedicalRecordCommandHandler,
)
from app.features.medical_records.application.commands.upload_medical_document.upload_medical_document_command import (
    UploadMedicalDocumentCommand,
)
from app.features.medical_records.application.commands.upload_medical_document.upload_medical_document_command_handler import (
    UploadMedicalDocumentCommandHandler,
)
from app.features.medical_records.application.dtos.new_record_input import NewRecordInput
from app.features.medical_records.application.queries.get_record_attachment.get_record_attachment_query import (
    GetRecordAttachmentQuery,
)
from app.features.medical_records.application.queries.get_record_attachment.get_record_attachment_query_handler import (
    GetRecordAttachmentQueryHandler,
)
from app.features.medical_records.application.queries.list_medical_records.list_medical_records_query import (
    ListMedicalRecordsQuery,
)
from app.features.medical_records.application.queries.list_medical_records.list_medical_records_query_handler import (
    ListMedicalRecordsQueryHandler,
)
from app.features.medical_records.presentation.dependencies import (
    get_add_medical_record_command_handler,
    get_delete_medical_record_command_handler,
    get_list_medical_records_query_handler,
    get_record_attachment_query_handler,
    get_upload_medical_document_command_handler,
)
from app.features.medical_records.presentation.mappers import MedicalRecordsPresentationMapper
from app.features.medical_records.presentation.requests.add_record_request import AddRecordRequest
from app.features.medical_records.presentation.responses.medical_record_response import (
    MedicalRecordResponse,
)
from app.shared.actor import Actor

router = APIRouter()


One = APIResponse[MedicalRecordResponse]


@router.get(
    "/{dog_id}/records",
    response_model=APIResponse[list[MedicalRecordResponse]],
    summary="List a Dog's medical records, newest first",
)
async def list_records(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: ListMedicalRecordsQueryHandler = Depends(get_list_medical_records_query_handler),
) -> APIResponse[list[MedicalRecordResponse]]:
    records = await handler.handle(ListMedicalRecordsQuery(actor=actor, dog_id=dog_id))
    return APIResponse(
        message="Medical records retrieved successfully",
        data=[MedicalRecordsPresentationMapper.to_medical_record_response(r) for r in records],
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
    handler: AddMedicalRecordCommandHandler = Depends(get_add_medical_record_command_handler),
) -> One:
    record = await handler.handle(
        AddMedicalRecordCommand(
            actor=actor, dog_id=dog_id, data=NewRecordInput(**payload.model_dump())
        )
    )
    return APIResponse(
        message="Medical record added",
        data=MedicalRecordsPresentationMapper.to_medical_record_response(record),
    )


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
    handler: UploadMedicalDocumentCommandHandler = Depends(
        get_upload_medical_document_command_handler
    ),
) -> One:
    record = await handler.handle(
        UploadMedicalDocumentCommand(
            actor=actor,
            dog_id=dog_id,
            title=title,
            content=await read_upload(file),
            content_type=file.content_type,
            max_bytes=settings.MAX_UPLOAD_BYTES,
        )
    )
    return APIResponse(
        message="Document uploaded",
        data=MedicalRecordsPresentationMapper.to_medical_record_response(record),
    )


@router.get(
    "/{dog_id}/records/{record_id}/attachment",
    response_class=Response,
    summary="Download a record's attachment",
)
async def get_attachment(
    dog_id: str,
    record_id: str,
    actor: Actor = Depends(get_actor),
    handler: GetRecordAttachmentQueryHandler = Depends(get_record_attachment_query_handler),
) -> Response:
    return file_response(
        await handler.handle(
            GetRecordAttachmentQuery(actor=actor, dog_id=dog_id, record_id=record_id)
        )
    )


@router.delete(
    "/{dog_id}/records/{record_id}",
    response_model=APIResponse[None],
    summary="Delete a medical record I authored",
)
async def delete_record(
    dog_id: str,
    record_id: str,
    actor: Actor = Depends(get_actor),
    handler: DeleteMedicalRecordCommandHandler = Depends(get_delete_medical_record_command_handler),
) -> APIResponse[None]:
    await handler.handle(
        DeleteMedicalRecordCommand(actor=actor, dog_id=dog_id, record_id=record_id)
    )
    return APIResponse(message="Medical record deleted", data=None)
