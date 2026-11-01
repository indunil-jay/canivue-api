from app.features.community.application.dtos.disease_community_output_dto import (
    DiseaseCommunityOutputDTO,
)
from app.features.community.domain.entities.disease_community import DiseaseCommunity


class DiseaseCommunityDTOMapper:
    @staticmethod
    def to_output_dto(entity: DiseaseCommunity) -> DiseaseCommunityOutputDTO:
        return DiseaseCommunityOutputDTO(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
