from dataclasses import dataclass

from app.features.community.application.dtos.disease_community_output_dto import (
    DiseaseCommunityOutputDTO,
)


@dataclass(frozen=True)
class CommunityView:
    community: DiseaseCommunityOutputDTO
    member_count: int
    joined: bool
