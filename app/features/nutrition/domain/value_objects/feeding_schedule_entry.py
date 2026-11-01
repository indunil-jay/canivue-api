from dataclasses import dataclass


@dataclass(frozen=True)
class FeedingScheduleEntry:
    time: str
    food_name: str
    portion_grams: int
