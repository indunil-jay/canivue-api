from pydantic import BaseModel


class ChangePlanRequest(BaseModel):
    plan_id: str
