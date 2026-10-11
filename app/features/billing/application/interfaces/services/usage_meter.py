from datetime import datetime
from typing import Protocol

from app.features.billing.domain.value_objects.usage import Usage


class UsageMeterProtocol(Protocol):
    """Counts what a user has actually used, from the modules that own the data."""

    async def measure(self, user_id: int, since: datetime) -> Usage: ...
