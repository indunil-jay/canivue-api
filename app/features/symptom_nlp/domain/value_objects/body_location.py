from dataclasses import dataclass


@dataclass
class BodyLocation:
    part: str
    side: str | None = None
