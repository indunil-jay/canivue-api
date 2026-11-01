from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Vaccination:
    name: str
    date_given: date
    next_due_date: date | None = None
