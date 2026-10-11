from app.features.devices.application.dtos.smart_collar_output_dto import SmartCollarOutputDTO
from app.features.devices.domain.entities.smart_collar import SmartCollar


class SmartCollarDTOMapper:
    @staticmethod
    def to_output_dto(entity: SmartCollar) -> SmartCollarOutputDTO:
        return SmartCollarOutputDTO(
            id=entity.id,
            dog_id=entity.dog_id,
            name=entity.name,
            state=entity.state,
            battery_percent=entity.battery_percent,
            last_synced_at=entity.last_synced_at,
            firmware_version=entity.firmware_version,
            sync_history=entity.sync_history,
            granted_permissions=entity.granted_permissions,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            is_paired=entity.is_paired,
        )
