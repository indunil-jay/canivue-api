from dataclasses import dataclass
from datetime import datetime

from app.features.messaging.domain.enums.message_sender import MessageSender
from app.shared.entity import BaseEntity


@dataclass
class Conversation(BaseEntity):
    owner_id: int = 0
    owner_name: str = ""
    vet_id: str = ""
    vet_user_id: int = 0
    vet_name: str = ""
    last_message_preview: str = ""
    last_message_at: datetime | None = None

    def side_of(self, user_id: int) -> MessageSender | None:
        if user_id == self.owner_id:
            return MessageSender.OWNER
        if user_id == self.vet_user_id:
            return MessageSender.VET
        return None

    def other_user_id(self, side: MessageSender) -> int:
        return self.vet_user_id if side == MessageSender.OWNER else self.owner_id
