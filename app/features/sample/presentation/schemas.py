from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CreateSampleRequest(BaseModel):
    """HTTP Request schema for creating a sample."""
    title: str = Field(..., min_length=1, max_length=255, description="Unique title of the sample")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")


class UpdateSampleRequest(BaseModel):
    """HTTP Request schema for updating a sample."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class SampleResponse(BaseModel):
    """HTTP Response schema for sample data."""
    id: str
    title: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }
