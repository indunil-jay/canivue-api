from typing import Optional
from app.features.sample.domain.entities import SampleItem
from app.shared.repository import BaseRepositoryProtocol


class SampleRepositoryProtocol(BaseRepositoryProtocol[SampleItem, str]):
    """Abstract Repository Interface defining storage operations for SampleItem."""

    async def get_by_title(self, title: str) -> Optional[SampleItem]:
        """Fetch a single sample by its title."""
        ...
