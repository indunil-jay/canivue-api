from enum import Enum


class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
