from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class CreateSampleDTO:
    """Input DTO for creating a new sample."""
    title: str
    description: Optional[str] = None


@dataclass(frozen=True)
class UpdateSampleDTO:
    """Input DTO for updating an existing sample."""
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


@dataclass(frozen=True)
class SampleOutputDTO:
    """Output DTO returned from application use cases."""
    id: str
    title: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
