from fastapi import Depends

from app.features.appointments.application.interfaces.repositories.appointment_repository import (
    AppointmentRepositoryProtocol,
)
from app.features.appointments.presentation.dependencies import get_appointment_repository
from app.features.assessments.application.interfaces.repositories.prediction_repository import (
    PredictionRepositoryProtocol,
)
from app.features.assessments.presentation.dependencies import get_prediction_repository
from app.features.dogs.application.interfaces.repositories.dog_repository import (
    DogRepositoryProtocol,
)
from app.features.dogs.presentation.dependencies import get_dog_repository
from app.features.messaging.application.interfaces.repositories.conversation_repository import (
    ConversationRepositoryProtocol,
)
from app.features.messaging.presentation.dependencies import get_conversation_repository
from app.features.vet_portal.application.queries.get_vet_dashboard.get_vet_dashboard_query_handler import (
    GetVetDashboardQueryHandler,
)
from app.features.vet_portal.application.queries.list_my_patients.list_my_patients_query_handler import (
    ListMyPatientsQueryHandler,
)
from app.features.vet_portal.application.services.vet_caseload import VetCaseload


def get_vet_caseload(
    appointments: AppointmentRepositoryProtocol = Depends(get_appointment_repository),
    dogs: DogRepositoryProtocol = Depends(get_dog_repository),
    predictions: PredictionRepositoryProtocol = Depends(get_prediction_repository),
) -> VetCaseload:
    return VetCaseload(appointments, dogs, predictions)


def get_vet_dashboard_query_handler(
    caseload: VetCaseload = Depends(get_vet_caseload),
    conversations: ConversationRepositoryProtocol = Depends(get_conversation_repository),
) -> GetVetDashboardQueryHandler:
    return GetVetDashboardQueryHandler(caseload, conversations)


def get_list_my_patients_query_handler(
    caseload: VetCaseload = Depends(get_vet_caseload),
) -> ListMyPatientsQueryHandler:
    return ListMyPatientsQueryHandler(caseload)
