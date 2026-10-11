from enum import Enum


class TimelineEventType(str, Enum):
    VACCINATION = "vaccination"
    MEDICATION = "medication"
    WEIGHT_CHANGE = "weightChange"
    DIAGNOSIS = "diagnosis"
    APPOINTMENT = "appointment"
    AI_PREDICTION = "aiPrediction"
    HEALTH_ALERT = "healthAlert"
    SENSOR_EVENT = "sensorEvent"
