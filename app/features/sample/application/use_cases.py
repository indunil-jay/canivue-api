from datetime import datetime, timezone
from typing import List
from app.features.sample.application.dtos import (
    CreateSampleDTO,
    SampleOutputDTO,
    UpdateSampleDTO,
)
from app.features.sample.domain.entities import SampleItem
from app.features.sample.domain.exceptions import (
    SampleNotFoundException,
    SampleTitleAlreadyExistsException,
)
from app.features.sample.domain.repositories import SampleRepositoryProtocol


def _to_output_dto(entity: SampleItem) -> SampleOutputDTO:
    """Helper mapper to convert domain entity to output DTO."""
    return SampleOutputDTO(
        id=entity.id,
        title=entity.title,
        description=entity.description,
        is_active=entity.is_active,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


class CreateSampleUseCase:
    """Use case for creating a new sample entity."""

    def __init__(self, repository: SampleRepositoryProtocol):
        self.repository = repository

    async def execute(self, dto: CreateSampleDTO) -> SampleOutputDTO:
        # Check uniqueness business rule
        existing = await self.repository.get_by_title(dto.title)
        if existing:
            raise SampleTitleAlreadyExistsException(dto.title)

        entity = SampleItem(
            title=dto.title,
            description=dto.description,
        )
        saved = await self.repository.create(entity)
        return _to_output_dto(saved)


class GetSampleByIdUseCase:
    """Use case for retrieving a sample entity by ID."""

    def __init__(self, repository: SampleRepositoryProtocol):
        self.repository = repository

    async def execute(self, sample_id: str) -> SampleOutputDTO:
        entity = await self.repository.get_by_id(sample_id)
        if not entity:
            raise SampleNotFoundException(sample_id)
        return _to_output_dto(entity)


class ListSamplesUseCase:
    """Use case for querying paginated sample entities."""

    def __init__(self, repository: SampleRepositoryProtocol):
        self.repository = repository

    async def execute(self, skip: int = 0, limit: int = 100) -> List[SampleOutputDTO]:
        entities = await self.repository.list_all(skip=skip, limit=limit)
        return [_to_output_dto(e) for e in entities]


class UpdateSampleUseCase:
    """Use case for modifying a sample entity."""

    def __init__(self, repository: SampleRepositoryProtocol):
        self.repository = repository

    async def execute(self, sample_id: str, dto: UpdateSampleDTO) -> SampleOutputDTO:
        entity = await self.repository.get_by_id(sample_id)
        if not entity:
            raise SampleNotFoundException(sample_id)

        if dto.title is not None and dto.title != entity.title:
            existing = await self.repository.get_by_title(dto.title)
            if existing and existing.id != sample_id:
                raise SampleTitleAlreadyExistsException(dto.title)
            entity.title = dto.title

        if dto.description is not None:
            entity.description = dto.description

        if dto.is_active is not None:
            if dto.is_active:
                entity.activate()
            else:
                entity.deactivate()

        entity.updated_at = datetime.now(timezone.utc)
        updated = await self.repository.update(entity)
        return _to_output_dto(updated)


class DeleteSampleUseCase:
    """Use case for removing a sample entity."""

    def __init__(self, repository: SampleRepositoryProtocol):
        self.repository = repository

    async def execute(self, sample_id: str) -> bool:
        entity = await self.repository.get_by_id(sample_id)
        if not entity:
            raise SampleNotFoundException(sample_id)
        return await self.repository.delete(sample_id)
