from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.devices.application.commands.disconnect_collar.disconnect_collar_command_handler import (
    DisconnectCollarCommandHandler,
)
from app.features.devices.application.commands.pair_collar.pair_collar_command_handler import (
    PairCollarCommandHandler,
)
from app.features.devices.application.commands.rename_collar.rename_collar_command_handler import (
    RenameCollarCommandHandler,
)
from app.features.devices.application.commands.sync_collar.sync_collar_command_handler import (
    SyncCollarCommandHandler,
)
from app.features.devices.application.interfaces.repositories.smart_collar_repository import (
    SmartCollarRepositoryProtocol,
)
from app.features.devices.application.queries.get_collar.get_collar_query_handler import (
    GetCollarQueryHandler,
)
from app.features.devices.infrastructure.persistence.repositories.smart_collar_repository import (
    SqlAlchemySmartCollarRepository,
)
from app.features.dogs.application.services.dog_access import DogAccess
from app.features.dogs.presentation.dependencies import get_dog_access


def get_collar_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SmartCollarRepositoryProtocol:
    return SqlAlchemySmartCollarRepository(session=session)


def get_disconnect_collar_command_handler(
    collars: SmartCollarRepositoryProtocol = Depends(get_collar_repository),
    access: DogAccess = Depends(get_dog_access),
) -> DisconnectCollarCommandHandler:
    return DisconnectCollarCommandHandler(collars, access)


def get_collar_query_handler(
    collars: SmartCollarRepositoryProtocol = Depends(get_collar_repository),
    access: DogAccess = Depends(get_dog_access),
) -> GetCollarQueryHandler:
    return GetCollarQueryHandler(collars, access)


def get_pair_collar_command_handler(
    collars: SmartCollarRepositoryProtocol = Depends(get_collar_repository),
    access: DogAccess = Depends(get_dog_access),
) -> PairCollarCommandHandler:
    return PairCollarCommandHandler(collars, access)


def get_rename_collar_command_handler(
    collars: SmartCollarRepositoryProtocol = Depends(get_collar_repository),
    access: DogAccess = Depends(get_dog_access),
) -> RenameCollarCommandHandler:
    return RenameCollarCommandHandler(collars, access)


def get_sync_collar_command_handler(
    collars: SmartCollarRepositoryProtocol = Depends(get_collar_repository),
    access: DogAccess = Depends(get_dog_access),
) -> SyncCollarCommandHandler:
    return SyncCollarCommandHandler(collars, access)
