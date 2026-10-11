from pydantic import BaseModel


class BodyLocationSchema(BaseModel):
    part: str
    side: str | None = None
