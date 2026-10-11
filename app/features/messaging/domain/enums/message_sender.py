from enum import Enum


class MessageSender(str, Enum):
    OWNER = "owner"
    VET = "vet"
