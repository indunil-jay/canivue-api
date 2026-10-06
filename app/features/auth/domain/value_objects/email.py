import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        normalized = self.value.strip().lower()
        if not normalized or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", normalized):
            raise ValueError(f"Invalid email address: '{self.value}'")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
