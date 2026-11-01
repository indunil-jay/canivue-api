from datetime import datetime

from pydantic import BaseModel, Field


class CommunityPostResponse(BaseModel):
    id: str
    author_name: str
    author_initials: str
    is_veterinarian: bool
    community_id: str
    community_tag: str
    content: str
    created_at: datetime
    like_count: int
    comment_count: int = Field(0, description="Comments are not supported yet; always 0.")
    share_count: int
    liked_by_me: bool
    saved_by_me: bool
