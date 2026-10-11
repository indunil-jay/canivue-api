from enum import Enum


class ConsultationType(str, Enum):
    VIDEO = "video"
    IN_PERSON = "inPerson"
    CHAT = "chat"
