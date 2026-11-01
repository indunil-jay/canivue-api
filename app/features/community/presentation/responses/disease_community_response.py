from pydantic import BaseModel


class DiseaseCommunityResponse(BaseModel):
    id: str
    name: str
    description: str
    member_count: int
    joined: bool
