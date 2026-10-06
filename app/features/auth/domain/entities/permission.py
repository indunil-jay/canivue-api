from dataclasses import dataclass


@dataclass
class Permission:
    id: int | None
    name: str
    description: str | None = None
