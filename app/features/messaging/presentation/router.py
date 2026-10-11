from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.messaging.application.use_cases import (
    ConversationView,
    ListConversationsUseCase,
    ReadMessagesUseCase,
    SendMessageUseCase,
    StartConversationUseCase,
)
from app.features.messaging.domain.entities import MessageKind, MessageSender, MessageStatus
from app.features.messaging.presentation.dependencies import (
    get_list_conversations_use_case,
    get_read_messages_use_case,
    get_send_message_use_case,
    get_start_conversation_use_case,
)
from app.shared.actor import Actor
from app.shared.text import initials_of

router = APIRouter()


class StartConversationRequest(BaseModel):
    vet_id: str


class SendMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    kind: MessageKind = MessageKind.TEXT


class ConversationResponse(BaseModel):
    id: str
    vet_id: str
    vet_name: str
    vet_initials: str
    owner_name: str
    last_message_preview: str
    last_message_at: datetime | None
    unread_count: int
    online: bool = Field(False, description="Presence is not tracked yet; always false.")

    @classmethod
    def from_view(cls, view: ConversationView) -> "ConversationResponse":
        c = view.conversation
        return cls(
            id=c.id,
            vet_id=c.vet_id,
            vet_name=c.vet_name,
            vet_initials=initials_of(c.vet_name),
            owner_name=c.owner_name,
            last_message_preview=c.last_message_preview,
            last_message_at=c.last_message_at,
            unread_count=view.unread_count,
        )


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    sender: MessageSender
    text: str
    timestamp: datetime = Field(validation_alias="created_at")
    status: MessageStatus
    kind: MessageKind


@router.post(
    "",
    response_model=APIResponse[ConversationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Start (or reopen) my conversation with a veterinarian",
)
async def start_conversation(
    payload: StartConversationRequest,
    actor: Actor = Depends(get_actor),
    use_case: StartConversationUseCase = Depends(get_start_conversation_use_case),
) -> APIResponse[ConversationResponse]:
    view = await use_case.execute(actor, payload.vet_id)
    return APIResponse(message="Conversation ready", data=ConversationResponse.from_view(view))


@router.get(
    "", response_model=APIResponse[list[ConversationResponse]], summary="List my conversations"
)
async def list_conversations(
    actor: Actor = Depends(get_actor),
    use_case: ListConversationsUseCase = Depends(get_list_conversations_use_case),
) -> APIResponse[list[ConversationResponse]]:
    views = await use_case.execute(actor)
    return APIResponse(
        message="Conversations retrieved successfully",
        data=[ConversationResponse.from_view(v) for v in views],
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=APIResponse[list[MessageResponse]],
    summary="Read a conversation's messages, oldest first",
    description="Pass `after` (the timestamp of the newest message you hold) to poll for new ones. "
    "Reading marks the other party's messages as read.",
)
async def read_messages(
    conversation_id: str,
    after: datetime | None = None,
    limit: int = Query(200, ge=1, le=500),
    actor: Actor = Depends(get_actor),
    use_case: ReadMessagesUseCase = Depends(get_read_messages_use_case),
) -> APIResponse[list[MessageResponse]]:
    messages = await use_case.execute(actor, conversation_id, after, limit)
    return APIResponse(
        message="Messages retrieved successfully",
        data=[MessageResponse.model_validate(m) for m in messages],
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=APIResponse[MessageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
)
async def send_message(
    conversation_id: str,
    payload: SendMessageRequest,
    actor: Actor = Depends(get_actor),
    use_case: SendMessageUseCase = Depends(get_send_message_use_case),
) -> APIResponse[MessageResponse]:
    message = await use_case.execute(actor, conversation_id, payload.text, payload.kind)
    return APIResponse(
        message="Message sent successfully", data=MessageResponse.model_validate(message)
    )
