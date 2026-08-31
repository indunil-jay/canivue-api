import pytest
from app.features.sample.application.dtos import CreateSampleDTO, UpdateSampleDTO
from app.features.sample.application.use_cases import (
    CreateSampleUseCase,
    DeleteSampleUseCase,
    GetSampleByIdUseCase,
    ListSamplesUseCase,
    UpdateSampleUseCase,
)
from app.features.sample.domain.exceptions import (
    SampleNotFoundException,
    SampleTitleAlreadyExistsException,
)
from app.features.sample.infrastructure.repositories import SQLAlchemySampleRepository


@pytest.mark.asyncio
async def test_create_and_get_sample_use_case(db_session):
    repo = SQLAlchemySampleRepository(session=db_session)
    create_uc = CreateSampleUseCase(repository=repo)
    get_uc = GetSampleByIdUseCase(repository=repo)

    # 1. Create sample
    dto = CreateSampleDTO(title="Test Item", description="A sample description")
    created = await create_uc.execute(dto)

    assert created.id is not None
    assert created.title == "Test Item"
    assert created.description == "A sample description"
    assert created.is_active is True

    # 2. Get sample by ID
    fetched = await get_uc.execute(created.id)
    assert fetched.id == created.id
    assert fetched.title == "Test Item"


@pytest.mark.asyncio
async def test_duplicate_title_raises_exception(db_session):
    repo = SQLAlchemySampleRepository(session=db_session)
    create_uc = CreateSampleUseCase(repository=repo)

    dto = CreateSampleDTO(title="Unique Title", description="Description")
    await create_uc.execute(dto)

    with pytest.raises(SampleTitleAlreadyExistsException):
        await create_uc.execute(dto)


@pytest.mark.asyncio
async def test_update_and_delete_sample_use_case(db_session):
    repo = SQLAlchemySampleRepository(session=db_session)
    create_uc = CreateSampleUseCase(repository=repo)
    update_uc = UpdateSampleUseCase(repository=repo)
    delete_uc = DeleteSampleUseCase(repository=repo)
    get_uc = GetSampleByIdUseCase(repository=repo)

    created = await create_uc.execute(CreateSampleDTO(title="Item To Update"))

    # Update
    updated = await update_uc.execute(
        created.id,
        UpdateSampleDTO(title="Updated Title", is_active=False),
    )
    assert updated.title == "Updated Title"
    assert updated.is_active is False

    # Delete
    deleted = await delete_uc.execute(created.id)
    assert deleted is True

    # Verify not found after delete
    with pytest.raises(SampleNotFoundException):
        await get_uc.execute(created.id)
