from enum import Enum


class ReminderKind(str, Enum):
    VACCINATION = "vaccination"
    MEDICATION = "medication"
    GROOMING = "grooming"
    CHECKUP = "checkup"
    DEWORMING = "deworming"
