from pydantic import BaseModel


class ExtractedSpanSchema(BaseModel):
    entity: str
    text: str
    start: int
    end: int
    negated: bool = False
