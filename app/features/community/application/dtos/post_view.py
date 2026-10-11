from dataclasses import dataclass

from app.features.community.application.dtos.community_post_output_dto import CommunityPostOutputDTO


@dataclass(frozen=True)
class PostView:
    post: CommunityPostOutputDTO
    like_count: int
    liked_by_me: bool
    saved_by_me: bool
