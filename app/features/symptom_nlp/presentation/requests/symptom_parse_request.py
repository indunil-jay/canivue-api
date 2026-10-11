from pydantic import BaseModel, Field


class SymptomParseRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        description="Dog owner's informal, natural language symptom description",
        examples=["My dog has been scratching its left ear for three days and it is becoming red."],
    )
