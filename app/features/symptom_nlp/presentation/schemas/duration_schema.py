from pydantic import BaseModel


class DurationSchema(BaseModel):
    value: int
    unit: str
