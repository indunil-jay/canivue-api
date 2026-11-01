from pydantic import BaseModel, Field


class PublishPostRequest(BaseModel):
    community_id: str
    content: str = Field(..., min_length=1, max_length=5000)
