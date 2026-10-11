from dataclasses import dataclass


@dataclass(frozen=True)
class DogFacts:
    name: str
    breed: str
    age_years: int
    allergies: tuple[str, ...] = ()
    special_notes: str = ""
