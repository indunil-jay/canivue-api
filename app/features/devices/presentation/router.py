from fastapi import APIRouter, Depends

from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.devices.application.commands.disconnect_collar.disconnect_collar_command import (
    DisconnectCollarCommand,
)
from app.features.devices.application.commands.disconnect_collar.disconnect_collar_command_handler import (
    DisconnectCollarCommandHandler,
)
from app.features.devices.application.commands.pair_collar.pair_collar_command import (
    PairCollarCommand,
)
from app.features.devices.application.commands.pair_collar.pair_collar_command_handler import (
    PairCollarCommandHandler,
)
from app.features.devices.application.commands.rename_collar.rename_collar_command import (
    RenameCollarCommand,
)
from app.features.devices.application.commands.rename_collar.rename_collar_command_handler import (
    RenameCollarCommandHandler,
)
from app.features.devices.application.commands.sync_collar.sync_collar_command import (
    SyncCollarCommand,
)
from app.features.devices.application.commands.sync_collar.sync_collar_command_handler import (
    SyncCollarCommandHandler,
)
from app.features.devices.application.queries.get_collar.get_collar_query import GetCollarQuery
from app.features.devices.application.queries.get_collar.get_collar_query_handler import (
    GetCollarQueryHandler,
)
from app.features.devices.presentation.dependencies import (
    get_collar_query_handler,
    get_disconnect_collar_command_handler,
    get_pair_collar_command_handler,
    get_rename_collar_command_handler,
    get_sync_collar_command_handler,
)
from app.features.devices.presentation.requests.rename_collar_request import RenameCollarRequest
from app.features.devices.presentation.requests.sync_collar_request import SyncCollarRequest
from app.features.devices.presentation.responses.smart_collar_response import SmartCollarResponse
from app.shared.actor import Actor

router = APIRouter()


Collar = APIResponse[SmartCollarResponse]


def _ok(message: str, collar) -> Collar:
    return APIResponse(message=message, data=SmartCollarResponse.model_validate(collar))


@router.get("/{dog_id}/device", response_model=Collar, summary="Get a Dog's smart collar")
async def get_collar(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: GetCollarQueryHandler = Depends(get_collar_query_handler),
) -> Collar:
    return _ok(
        "Device retrieved successfully",
        await handler.handle(GetCollarQuery(actor=actor, dog_id=dog_id)),
    )


@router.post("/{dog_id}/device/pair", response_model=Collar, summary="Pair a collar with a Dog")
async def pair_collar(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: PairCollarCommandHandler = Depends(get_pair_collar_command_handler),
) -> Collar:
    return _ok("Device paired", await handler.handle(PairCollarCommand(actor=actor, dog_id=dog_id)))


@router.post(
    "/{dog_id}/device/disconnect", response_model=Collar, summary="Disconnect a Dog's collar"
)
async def disconnect_collar(
    dog_id: str,
    actor: Actor = Depends(get_actor),
    handler: DisconnectCollarCommandHandler = Depends(get_disconnect_collar_command_handler),
) -> Collar:
    return _ok(
        "Device disconnected",
        await handler.handle(DisconnectCollarCommand(actor=actor, dog_id=dog_id)),
    )


@router.patch("/{dog_id}/device", response_model=Collar, summary="Rename a Dog's collar")
async def rename_collar(
    dog_id: str,
    payload: RenameCollarRequest,
    actor: Actor = Depends(get_actor),
    handler: RenameCollarCommandHandler = Depends(get_rename_collar_command_handler),
) -> Collar:
    return _ok(
        "Device renamed",
        await handler.handle(RenameCollarCommand(actor=actor, dog_id=dog_id, name=payload.name)),
    )


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
    handler: SyncCollarCommandHandler = Depends(get_sync_collar_command_handler),
) -> Collar:
    payload = payload or SyncCollarRequest()
    collar = await handler.handle(
        SyncCollarCommand(
            actor=actor,
            dog_id=dog_id,
            records_synced=payload.records_synced,
            battery_percent=payload.battery_percent,
        )
    )
    return _ok("Device synced", collar)
