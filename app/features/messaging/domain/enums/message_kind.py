from enum import Enum


class MessageKind(str, Enum):
    TEXT = "text"
    CONSULTATION_SUMMARY = "consultationSummary"
