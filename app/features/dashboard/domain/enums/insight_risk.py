from enum import Enum


class InsightRisk(str, Enum):
    NORMAL = "normal"
    MONITORING = "monitoring"
    ELEVATED = "elevated"
