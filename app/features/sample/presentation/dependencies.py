from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.sample.application.use_cases import (
    CreateSampleUseCase,
    DeleteSampleUseCase,
    GetSampleByIdUseCase,
    ListSamplesUseCase,
    UpdateSampleUseCase,
)
from app.features.sample.domain.repositories import SampleRepositoryProtocol
from app.features.sample.infrastructure.repositories import SQLAlchemySampleRepository


def get_sample_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SampleRepositoryProtocol:
    """Dependency provider for the SampleRepository interface."""
    return SQLAlchemySampleRepository(session=session)


def get_create_sample_use_case(
    repo: SampleRepositoryProtocol = Depends(get_sample_repository),
) -> CreateSampleUseCase:
    return CreateSampleUseCase(repository=repo)


def get_get_sample_by_id_use_case(
    repo: SampleRepositoryProtocol = Depends(get_sample_repository),
) -> GetSampleByIdUseCase:
    return GetSampleByIdUseCase(repository=repo)


def get_list_samples_use_case(
    repo: SampleRepositoryProtocol = Depends(get_sample_repository),
) -> ListSamplesUseCase:
    return ListSamplesUseCase(repository=repo)


def get_update_sample_use_case(
    repo: SampleRepositoryProtocol = Depends(get_sample_repository),
) -> UpdateSampleUseCase:
    return UpdateSampleUseCase(repository=repo)


def get_delete_sample_use_case(
    repo: SampleRepositoryProtocol = Depends(get_sample_repository),
) -> DeleteSampleUseCase:
    return DeleteSampleUseCase(repository=repo)
