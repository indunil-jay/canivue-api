from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class GetInboxQuery:
    actor: Actor
    limit: int = 100
