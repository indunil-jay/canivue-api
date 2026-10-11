from dataclasses import dataclass

from app.features.community.domain.enums.reaction_kind import ReactionKind
from app.shared.actor import Actor


@dataclass(frozen=True)
class TogglePostReactionCommand:
    actor: Actor
    post_id: str
    kind: ReactionKind
