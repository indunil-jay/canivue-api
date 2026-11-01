from app.features.community.application.dtos.community_view import CommunityView
from app.features.community.application.dtos.post_view import PostView
from app.features.community.presentation.responses.community_post_response import (
    CommunityPostResponse,
)
from app.features.community.presentation.responses.disease_community_response import (
    DiseaseCommunityResponse,
)
from app.shared.text import initials_of


class CommunityPresentationMapper:
    @staticmethod
    def to_community_post_response(view: PostView) -> CommunityPostResponse:
        p = view.post
        return CommunityPostResponse(
            id=p.id,
            author_name=p.author_name,
            author_initials=initials_of(p.author_name),
            is_veterinarian=p.is_veterinarian,
            community_id=p.community_id,
            community_tag=p.community_tag,
            content=p.content,
            created_at=p.created_at,
            like_count=view.like_count,
            share_count=p.share_count,
            liked_by_me=view.liked_by_me,
            saved_by_me=view.saved_by_me,
        )

    @staticmethod
    def to_disease_community_response(view: CommunityView) -> DiseaseCommunityResponse:
        c = view.community
        return DiseaseCommunityResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            member_count=view.member_count,
            joined=view.joined,
        )
