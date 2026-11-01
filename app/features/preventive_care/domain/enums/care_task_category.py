from enum import Enum


class CareTaskCategory(str, Enum):
    VACCINATION = "vaccination"
    DEWORMING = "deworming"
    FLEA_TICK = "fleaTick"
    DENTAL = "dental"
    GROOMING = "grooming"
    ANNUAL_CHECK = "annualCheck"
    WEIGHT_GOAL = "weightGoal"
    MEDICATION = "medication"
