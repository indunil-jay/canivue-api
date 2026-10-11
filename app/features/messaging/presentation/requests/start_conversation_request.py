from pydantic import BaseModel


class StartConversationRequest(BaseModel):
    vet_id: str
