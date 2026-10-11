from app.features.messaging.application.dtos.conversation_view import ConversationView
from app.features.messaging.presentation.responses.conversation_response import ConversationResponse
from app.shared.text import initials_of


class MessagingPresentationMapper:
    @staticmethod
    def to_conversation_response(view: ConversationView) -> ConversationResponse:
        c = view.conversation
        return ConversationResponse(
            id=c.id,
            vet_id=c.vet_id,
            vet_name=c.vet_name,
            vet_initials=initials_of(c.vet_name),
            owner_name=c.owner_name,
            last_message_preview=c.last_message_preview,
            last_message_at=c.last_message_at,
            unread_count=view.unread_count,
        )
