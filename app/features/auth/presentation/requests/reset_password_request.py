from pydantic import BaseModel, Field


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, description="Password reset token received via email")
    new_password: str = Field(min_length=8, description="New account password (minimum 8 characters)")
