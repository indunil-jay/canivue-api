from dataclasses import dataclass
from typing import Optional
from app.shared.entity import BaseEntity


@dataclass
class SampleItem(BaseEntity):
    """Domain Entity representing a Sample resource."""

    title: str = ""
    description: Optional[str] = None
    is_active: bool = True

    def activate(self) -> None:
        """Domain business logic method: activate item."""
        self.is_active = True

    def deactivate(self) -> None:
        """Domain business logic method: deactivate item."""
        self.is_active = False
