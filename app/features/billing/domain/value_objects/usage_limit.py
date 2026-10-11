from dataclasses import dataclass


@dataclass(frozen=True)
class UsageLimit:
    label: str
    used: int
    limit: int
