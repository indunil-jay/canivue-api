from dataclasses import dataclass

from app.shared.entity import BaseEntity


@dataclass
class DiseaseCommunity(BaseEntity):
    name: str = ""
    description: str = ""
