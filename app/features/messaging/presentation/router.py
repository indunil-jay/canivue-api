from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from app.core.response import APIResponse
from app.features.auth.presentation.dependencies import get_actor
from app.features.messaging.application.commands.read_messages.read_messages_command import (
    ReadMessagesCommand,
)
from app.features.messaging.application.commands.read_messages.read_messages_command_handler import (
    ReadMessagesCommandHandler,
)
from app.features.messaging.application.commands.send_message.send_message_command import (
    SendMessageCommand,
)
from app.features.messaging.application.commands.send_message.send_message_command_handler import (
    SendMessageCommandHandler,
)
from app.features.messaging.application.commands.start_conversation.start_conversation_command import (
    StartConversationCommand,
)
from app.features.messaging.application.commands.start_conversation.start_conversation_command_handler import (
    StartConversationCommandHandler,
)
from app.features.messaging.application.queries.list_conversations.list_conversations_query import (
    ListConversationsQuery,
)
from app.features.messaging.application.queries.list_conversations.list_conversations_query_handler import (
    ListConversationsQueryHandler,
)
from app.features.messaging.presentation.dependencies import (
    get_list_conversations_query_handler,
    get_read_messages_command_handler,
    get_send_message_command_handler,
    get_start_conversation_command_handler,
)
from app.features.messaging.presentation.mappers import MessagingPresentationMapper
from app.features.messaging.presentation.requests.send_message_request import SendMessageRequest
from app.features.messaging.presentation.requests.start_conversation_request import (
    StartConversationRequest,
)
from app.features.messaging.presentation.responses.conversation_response import ConversationResponse
from app.features.messaging.presentation.responses.message_response import MessageResponse
from app.shared.actor import Actor

router = APIRouter()


@router.post(
    "",
    response_model=APIResponse[ConversationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Start (or reopen) my conversation with a veterinarian",
)
async def start_conversation(
    payload: StartConversationRequest,
    actor: Actor = Depends(get_actor),
    handler: StartConversationCommandHandler = Depends(get_start_conversation_command_handler),
) -> APIResponse[ConversationResponse]:
    view = await handler.handle(StartConversationCommand(actor=actor, vet_id=payload.vet_id))
    return APIResponse(
        message="Conversation ready",
        data=MessagingPresentationMapper.to_conversation_response(view),
    )


@router.get(
    "", response_model=APIResponse[list[ConversationResponse]], summary="List my conversations"
)
async def list_conversations(
    actor: Actor = Depends(get_actor),
    handler: ListConversationsQueryHandler = Depends(get_list_conversations_query_handler),
) -> APIResponse[list[ConversationResponse]]:
    views = await handler.handle(ListConversationsQuery(actor=actor))
    return APIResponse(
        message="Conversations retrieved successfully",
        data=[MessagingPresentationMapper.to_conversation_response(v) for v in views],
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
    handler: ReadMessagesCommandHandler = Depends(get_read_messages_command_handler),
) -> APIResponse[list[MessageResponse]]:
    messages = await handler.handle(
        ReadMessagesCommand(actor=actor, conversation_id=conversation_id, after=after, limit=limit)
    )
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
    handler: SendMessageCommandHandler = Depends(get_send_message_command_handler),
) -> APIResponse[MessageResponse]:
    message = await handler.handle(
        SendMessageCommand(
            actor=actor, conversation_id=conversation_id, text=payload.text, kind=payload.kind
        )
    )
    return APIResponse(
        message="Message sent successfully", data=MessageResponse.model_validate(message)
    )
