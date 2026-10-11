from dataclasses import dataclass


@dataclass
class ExtractedSpan:
    entity: str
    text: str
    start: int
    end: int
    negated: bool = False
