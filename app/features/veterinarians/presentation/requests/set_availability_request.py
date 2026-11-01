from pydantic import BaseModel


class SetAvailabilityRequest(BaseModel):
    available: bool
