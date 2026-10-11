from dataclasses import dataclass

from app.features.community.domain.entities.community_post import CommunityPost


@dataclass(frozen=True)
class PostView:
    post: CommunityPost
    like_count: int
    liked_by_me: bool
    saved_by_me: bool
