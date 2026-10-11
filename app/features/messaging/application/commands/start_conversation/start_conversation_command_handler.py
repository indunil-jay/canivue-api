from app.features.messaging.application.commands.start_conversation.start_conversation_command import (
    StartConversationCommand,
)
from app.features.messaging.application.dtos.conversation_view import ConversationView
from app.features.messaging.application.interfaces.repositories.conversation_repository import (
    ConversationRepositoryProtocol,
)
from app.features.messaging.domain.entities.conversation import Conversation
from app.features.veterinarians.application.interfaces.repositories.vet_profile_repository import (
    VetProfileRepositoryProtocol,
)
from app.features.veterinarians.domain.exceptions import VeterinarianNotFoundError


class StartConversationCommandHandler:
    def __init__(
        self, conversations: ConversationRepositoryProtocol, vets: VetProfileRepositoryProtocol
    ):
        self._conversations = conversations
        self._vets = vets

    async def handle(self, command: StartConversationCommand) -> ConversationView:
        vet = await self._vets.get_by_id(command.vet_id)
        if vet is None or not vet.verified or vet.user_id == command.actor.id:
            raise VeterinarianNotFoundError()
        existing = await self._conversations.get_for_pair(command.actor.id, vet.id)
        conversation = existing or await self._conversations.create(
            Conversation(
                owner_id=command.actor.id,
                owner_name=command.actor.display_name,
                vet_id=vet.id,
                vet_user_id=vet.user_id,
                vet_name=vet.name,
            )
        )
        return ConversationView(conversation, unread_count=0)
