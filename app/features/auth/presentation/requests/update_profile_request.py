from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    address: str | None = Field(None, max_length=255)
    emergency_contact: str | None = Field(None, max_length=255)


class UpdatePrivacySettingsRequest(BaseModel):
    share_with_vet: bool | None = None
    share_anonymized_research: bool | None = None
    location_services: bool | None = None
    two_factor_enabled: bool | None = None


class PrivacySettingsResponseData(BaseModel):
    share_with_vet: bool
    share_anonymized_research: bool
    location_services: bool
    two_factor_enabled: bool
