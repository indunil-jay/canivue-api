from datetime import datetime, timedelta, timezone

from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.messaging.application.interfaces.repositories.conversation_repository import (
    ConversationRepositoryProtocol,
)
from app.features.vet_portal.application.dtos.recent_message_preview import RecentMessagePreview
from app.features.vet_portal.application.dtos.schedule_entry import ScheduleEntry
from app.features.vet_portal.application.dtos.vet_dashboard_summary import VetDashboardSummary
from app.features.vet_portal.application.queries.get_vet_dashboard.get_vet_dashboard_query import (
    GetVetDashboardQuery,
)
from app.features.vet_portal.application.services.vet_caseload import VetCaseload
from app.features.veterinarians.domain.enums.consultation_type import ConsultationType

NEW_PATIENT_WINDOW = timedelta(days=7)


RECENT_MESSAGE_LIMIT = 5


_TYPE_LABELS = {
    ConsultationType.VIDEO: "Video Call",
    ConsultationType.IN_PERSON: "In Person",
    ConsultationType.CHAT: "Chat",
}


class GetVetDashboardQueryHandler:
    def __init__(self, caseload: VetCaseload, conversations: ConversationRepositoryProtocol):
        self._caseload = caseload
        self._conversations = conversations

    async def handle(self, query: GetVetDashboardQuery) -> VetDashboardSummary:
        now = datetime.now(timezone.utc)
        appointments = await self._caseload.appointments_of(query.actor)
        patients = await self._caseload.patients_of(query.actor)

        first_seen: dict[str, datetime] = {}
        for a in appointments:
            first_seen[a.dog_id] = min(first_seen.get(a.dog_id, a.created_at), a.created_at)

        conversations = [
            c
            for c in await self._conversations.list_for_user(query.actor.id)
            if c.vet_user_id == query.actor.id and c.last_message_at
        ]
        return VetDashboardSummary(
            vet_name=query.actor.display_name,
            today_schedule=[
                ScheduleEntry(
                    appointment_id=a.id,
                    time=a.date_time,
                    owner_name=a.owner_name,
                    dog_name=a.dog_name,
                    type=_TYPE_LABELS[a.consultation_type],
                    confirmed=a.status != AppointmentStatus.REQUESTED,
                )
                for a in appointments
                if a.date_time.date() == now.date() and a.status != AppointmentStatus.NO_SHOW
            ],
            waiting_consultation_count=sum(
                1 for a in appointments if a.status == AppointmentStatus.REQUESTED
            ),
            critical_alert_count=sum(1 for p in patients if p.has_critical_alert),
            new_patient_count=sum(
                1 for seen in first_seen.values() if now - seen <= NEW_PATIENT_WINDOW
            ),
            recent_messages=[
                RecentMessagePreview(c.id, c.owner_name, c.last_message_preview, c.last_message_at)
                for c in conversations[:RECENT_MESSAGE_LIMIT]
            ],
        )
