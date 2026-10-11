from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.core.exceptions import ForbiddenException, NotFoundException
from app.shared.entity import BaseEntity


class MessageSender(str, Enum):
    OWNER = "owner"
    VET = "vet"


class MessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class MessageKind(str, Enum):
    TEXT = "text"
    CONSULTATION_SUMMARY = "consultationSummary"


class ConversationNotFoundError(NotFoundException):
    def __init__(self) -> None:
        super().__init__(message="Conversation not found.")


class SummaryNotAllowedError(ForbiddenException):
    def __init__(self) -> None:
        super().__init__(message="Only the veterinarian can post a consultation summary.")


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


@dataclass
class Message(BaseEntity):
    conversation_id: str = ""
    sender: MessageSender = MessageSender.OWNER
    text: str = ""
    kind: MessageKind = MessageKind.TEXT
    status: MessageStatus = MessageStatus.SENT
