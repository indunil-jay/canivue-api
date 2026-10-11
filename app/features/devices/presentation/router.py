from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.devices.application.use_cases import (
    DisconnectCollarUseCase,
    GetCollarUseCase,
    PairCollarUseCase,
    RenameCollarUseCase,
    SyncCollarUseCase,
)
from app.features.devices.domain.entities import (
    CollarConnectionState,
    SmartCollarRepositoryProtocol,
)
from app.features.devices.infrastructure.persistence.repositories import (
    SqlAlchemySmartCollarRepository,
)
from app.features.dogs.application.access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access
from app.shared.actor import Actor

router = APIRouter()


class RenameCollarRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class SyncCollarRequest(BaseModel):
    records_synced: int = Field(0, ge=0)
    battery_percent: int | None = Field(None, ge=0, le=100)


class SyncEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    records_synced: int


class SmartCollarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dog_id: str
    name: str
    state: CollarConnectionState
    battery_percent: int | None
    last_synced_at: datetime | None
    firmware_version: str
    sync_history: list[SyncEventResponse]
    granted_permissions: list[str]


Collar = APIResponse[SmartCollarResponse]


def get_collar_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SmartCollarRepositoryProtocol:
    return SqlAlchemySmartCollarRepository(session=session)


def _provider(use_case_cls):
    def provide(
        collars: SmartCollarRepositoryProtocol = Depends(get_collar_repository),
        access: DogAccess = Depends(get_dog_access),
    ):
        return use_case_cls(collars, access)

    return provide


def _ok(message: str, collar) -> Collar:
    return APIResponse(message=message, data=SmartCollarResponse.model_validate(collar))


@router.get("/{dog_id}/device", response_model=Collar, summary="Get a Dog's smart collar")
async def get_collar(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: GetCollarUseCase = Depends(_provider(GetCollarUseCase)),
) -> Collar:
    return _ok("Device retrieved successfully", await use_case.execute(actor, dog_id))


@router.post("/{dog_id}/device/pair", response_model=Collar, summary="Pair a collar with a Dog")
async def pair_collar(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: PairCollarUseCase = Depends(_provider(PairCollarUseCase)),
) -> Collar:
    return _ok("Device paired", await use_case.execute(actor, dog_id))


@router.post(
    "/{dog_id}/device/disconnect", response_model=Collar, summary="Disconnect a Dog's collar"
)
async def disconnect_collar(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    use_case: DisconnectCollarUseCase = Depends(_provider(DisconnectCollarUseCase)),
) -> Collar:
    return _ok("Device disconnected", await use_case.execute(actor, dog_id))


@router.patch("/{dog_id}/device", response_model=Collar, summary="Rename a Dog's collar")
async def rename_collar(
    dog_id: str,
    payload: RenameCollarRequest,
    actor: Actor = Depends(get_actor),
    use_case: RenameCollarUseCase = Depends(_provider(RenameCollarUseCase)),
) -> Collar:
    return _ok("Device renamed", await use_case.execute(actor, dog_id, payload.name))


@router.post(
    "/{dog_id}/device/sync",
    response_model=Collar,
    summary="Record a collar sync",
    description="Called when the app finishes pulling data from the collar; it may report "
    "how many readings were transferred and the collar's battery level.",
)
async def sync_collar(
    dog_id: str,
    payload: SyncCollarRequest | None = None,
    actor: Actor = Depends(get_actor),
    use_case: SyncCollarUseCase = Depends(_provider(SyncCollarUseCase)),
) -> Collar:
    payload = payload or SyncCollarRequest()
    collar = await use_case.execute(actor, dog_id, payload.records_synced, payload.battery_percent)
    return _ok("Device synced", collar)
