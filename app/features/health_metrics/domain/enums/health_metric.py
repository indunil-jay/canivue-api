from enum import Enum


class HealthMetric(str, Enum):
    HEART_RATE = "heartRate"
    ACTIVITY = "activity"
    SLEEP = "sleep"
    TEMPERATURE = "temperature"
    WEIGHT = "weight"
    HYDRATION = "hydration"
