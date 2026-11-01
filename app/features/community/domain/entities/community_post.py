from dataclasses import dataclass

from app.shared.entity import BaseEntity


@dataclass
class CommunityPost(BaseEntity):
    author_id: int = 0
    author_name: str = ""
    is_veterinarian: bool = False
    community_id: str = ""
    community_tag: str = ""
    content: str = ""
    share_count: int = 0
