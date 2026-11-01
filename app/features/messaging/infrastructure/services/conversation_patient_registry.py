from app.features.dogs.application.interfaces.services.patient_registry import (
    PatientRegistryProtocol,
)
from app.features.dogs.domain.entities.dog import Dog
from app.features.messaging.infrastructure.persistence.models.conversation_model import (
    ConversationModel,
)
from app.features.messaging.infrastructure.persistence.repositories.conversation_repository import (
    SqlAlchemyConversationRepository,
)


class ConversationPatientRegistry(SqlAlchemyConversationRepository, PatientRegistryProtocol):
    """A Dog is a veterinarian's patient when its owner has a conversation with them."""

    async def is_patient(self, vet_user_id: int, dog: Dog) -> bool:
        linked = await self.count(
            ConversationModel.vet_user_id == vet_user_id, ConversationModel.owner_id == dog.owner_id
        )
        return linked > 0
