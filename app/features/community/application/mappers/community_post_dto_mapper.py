from app.features.community.application.dtos.community_post_output_dto import CommunityPostOutputDTO
from app.features.community.domain.entities.community_post import CommunityPost


class CommunityPostDTOMapper:
    @staticmethod
    def to_output_dto(entity: CommunityPost) -> CommunityPostOutputDTO:
        return CommunityPostOutputDTO(
            id=entity.id,
            author_id=entity.author_id,
            author_name=entity.author_name,
            is_veterinarian=entity.is_veterinarian,
            community_id=entity.community_id,
            community_tag=entity.community_tag,
            content=entity.content,
            share_count=entity.share_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
