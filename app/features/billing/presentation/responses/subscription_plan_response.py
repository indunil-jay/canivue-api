from pydantic import BaseModel, ConfigDict


class SubscriptionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    price_monthly: float
    features: list[str]
