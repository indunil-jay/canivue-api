from dataclasses import dataclass

from app.shared.actor import Actor


@dataclass(frozen=True)
class GetRecordAttachmentQuery:
    actor: Actor
    dog_id: str
    record_id: str
