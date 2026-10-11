from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from app.core.exceptions import NotFoundException
from app.shared.entity import BaseEntity


class ReactionKind(str, Enum):
    LIKE = "like"
    SAVE = "save"


class CommunityNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Community not found.")


class PostNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Post not found.")


@dataclass
class DiseaseCommunity(BaseEntity):
    name: str = ""
    description: str = ""


@dataclass
class CommunityPost(BaseEntity):
    author_id: int = 0
    author_name: str = ""
    is_veterinarian: bool = False
    community_id: str = ""
    community_tag: str = ""
    content: str = ""
    share_count: int = 0


@dataclass(frozen=True)
class PostView:
    post: CommunityPost
    like_count: int
    liked_by_me: bool
    saved_by_me: bool


@dataclass(frozen=True)
class CommunityView:
    community: DiseaseCommunity
    member_count: int
    joined: bool


# The disease communities every installation starts with: (id, name, description).
DEFAULT_COMMUNITIES = [
    (
        "skin-allergies",
        "Skin Allergies",
        "Share experiences and vet-verified advice on allergies and dermatology.",
    ),
    ("arthritis", "Arthritis", "Support and tips for dogs with joint pain and mobility issues."),
    ("obesity", "Obesity", "Weight management, nutrition and exercise plans."),
    ("diabetes", "Diabetes", "Managing canine diabetes — insulin, diet and monitoring."),
    ("heart-conditions", "Heart Conditions", "Cardiac health, medication and lifestyle."),
    (
        "digestive-problems",
        "Digestive Problems",
        "GI issues, food sensitivities and diet transitions.",
    ),
]


class CommunityRepositoryProtocol(Protocol):
    async def get_community(self, community_id: str) -> DiseaseCommunity | None: ...

    async def list_communities(self) -> Sequence[DiseaseCommunity]: ...

    async def member_counts(self) -> dict[str, int]: ...

    async def joined_ids(self, user_id: int) -> set[str]: ...

    async def toggle_membership(self, community_id: str, user_id: int) -> None: ...

    async def add_post(self, post: CommunityPost) -> CommunityPost: ...

    async def get_post(self, post_id: str) -> CommunityPost | None: ...

    async def list_posts(
        self, community_id: str | None, saved_by: int | None, limit: int
    ) -> Sequence[CommunityPost]: ...

    async def like_counts(self, post_ids: Sequence[str]) -> dict[str, int]: ...

    async def reactions_of(self, user_id: int, post_ids: Sequence[str]) -> set[tuple[str, str]]:
        """The (post id, reaction kind) pairs this user has on those posts."""
        ...

    async def toggle_reaction(self, post_id: str, user_id: int, kind: ReactionKind) -> None: ...

    async def increment_shares(self, post_id: str) -> None: ...
