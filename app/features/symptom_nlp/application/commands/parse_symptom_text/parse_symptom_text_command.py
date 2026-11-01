from dataclasses import dataclass


@dataclass(frozen=True)
class ParseSymptomTextCommand:
    text: str
