from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class BaseEntity:
    """Base Domain Entity containing standard identity and timestamp fields."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
