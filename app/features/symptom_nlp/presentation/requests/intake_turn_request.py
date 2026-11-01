from pydantic import BaseModel, Field


class IntakeTurnRequest(BaseModel):
    message: str = Field(
        ..., min_length=1, description="Follow-up response or clarification from dog owner"
    )
