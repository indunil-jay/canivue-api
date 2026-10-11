from datetime import datetime, timezone

from app.features.symptom_nlp.application.commands.complete_intake_session.complete_intake_session_command import (
    CompleteIntakeSessionCommand,
)
from app.features.symptom_nlp.application.dtos.parse_symptom_output_dto import ParseSymptomOutputDTO
from app.features.symptom_nlp.application.interfaces.repositories.intake_session_repository import (
    IntakeSessionRepositoryProtocol,
)
from app.features.symptom_nlp.domain.exceptions import (
    IntakeSessionNotFoundException,
)


class CompleteIntakeSessionCommandHandler:
    def __init__(self, session_repo: IntakeSessionRepositoryProtocol):
        self.session_repo = session_repo

    async def handle(self, command: CompleteIntakeSessionCommand) -> ParseSymptomOutputDTO:
        session = await self.session_repo.get(command.session_id)
        if session is None:
            raise IntakeSessionNotFoundException(
                message=f"Intake session '{command.session_id}' not found."
            )

        session.status = "completed"
        session.is_complete = True
        session.updated_at = datetime.now(timezone.utc).isoformat()
        await self.session_repo.save(session)
        return ParseSymptomOutputDTO.from_entity(session.accumulated_parse)
