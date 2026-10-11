from enum import Enum


class ReactionKind(str, Enum):
    LIKE = "like"
    SAVE = "save"
