from pydantic import BaseModel


class StoredResponse(BaseModel):
    stored: int
