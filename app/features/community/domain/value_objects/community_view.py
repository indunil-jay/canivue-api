from dataclasses import dataclass

from app.features.community.domain.entities.disease_community import DiseaseCommunity


@dataclass(frozen=True)
class CommunityView:
    community: DiseaseCommunity
    member_count: int
    joined: bool
