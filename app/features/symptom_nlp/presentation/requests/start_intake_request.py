from pydantic import BaseModel, Field


class StartIntakeRequest(BaseModel):
    dog_id: str = Field(..., description="Unique canine identifier")
    initial_text: str = Field(
        ..., min_length=1, description="Initial symptom text reported by dog owner"
    )
