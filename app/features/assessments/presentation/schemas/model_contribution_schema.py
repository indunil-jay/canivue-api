from pydantic import BaseModel, ConfigDict


class ModelContributionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    model_name: str
    contribution_percent: float
