from typing import List, Optional, Protocol
from app.features.sample.domain.entities import SampleItem


class SampleRepositoryProtocol(Protocol):
    """Abstract Repository Interface defining storage operations for SampleItem."""

    async def get_by_id(self, sample_id: str) -> Optional[SampleItem]:
        """Fetch a single sample by its ID."""
        ...

    async def get_by_title(self, title: str) -> Optional[SampleItem]:
        """Fetch a single sample by its title."""
        ...

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[SampleItem]:
        """List samples with pagination."""
        ...

    async def create(self, item: SampleItem) -> SampleItem:
        """Persist a new sample."""
        ...

    async def update(self, item: SampleItem) -> SampleItem:
        """Update an existing sample."""
        ...

    async def delete(self, sample_id: str) -> bool:
        """Delete a sample by ID."""
        ...
