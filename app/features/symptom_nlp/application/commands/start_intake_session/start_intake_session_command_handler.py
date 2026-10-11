import uuid
from datetime import datetime, timezone

from app.features.symptom_nlp.application.commands.start_intake_session.start_intake_session_command import (
    StartIntakeSessionCommand,
)
from app.features.symptom_nlp.application.dtos.intake_session_output_dto import (
    IntakeSessionOutputDTO,
)
from app.features.symptom_nlp.application.interfaces.repositories.intake_session_repository import (
    IntakeSessionRepositoryProtocol,
)
from app.features.symptom_nlp.application.interfaces.services.nlp_symptom_engine import (
    NLPSymptomEngineProtocol,
)
from app.features.symptom_nlp.domain.entities.intake_session import IntakeSession
from app.features.symptom_nlp.domain.exceptions import (
    EmptySymptomTextException,
)
from app.features.symptom_nlp.domain.services.evaluate_missing_slots import evaluate_missing_slots
from app.features.symptom_nlp.domain.services.generate_clarifying_prompt import (
    generate_clarifying_prompt,
)
from app.features.symptom_nlp.domain.value_objects.intake_message import IntakeMessage


class StartIntakeSessionCommandHandler:
    def __init__(
        self,
        engine: NLPSymptomEngineProtocol,
        session_repo: IntakeSessionRepositoryProtocol,
    ):
        self.engine = engine
        self.session_repo = session_repo

    async def handle(self, command: StartIntakeSessionCommand) -> IntakeSessionOutputDTO:
        clean_text = command.initial_text.strip() if command.initial_text else ""
        if not clean_text:
            raise EmptySymptomTextException()

        now_str = datetime.now(timezone.utc).isoformat()
        parse_result = await self.engine.parse(clean_text)

        missing_slots = evaluate_missing_slots(parse_result)
        agent_message = generate_clarifying_prompt(parse_result, missing_slots, turn_count=1)

        is_emergency = parse_result.emergency_triage.is_critical
        status = "emergency_diverted" if is_emergency else "in_progress"
        is_complete = bool(is_emergency)

        session_id = f"intake_{uuid.uuid4().hex[:12]}"

        initial_msg = IntakeMessage(
            role="user",
            content=clean_text,
            created_at=now_str,
        )

        session = IntakeSession(
            session_id=session_id,
            dog_id=command.dog_id,
            status=status,
            turn_count=1,
            messages=[initial_msg],
            accumulated_parse=parse_result,
            missing_slots=missing_slots,
            agent_message=agent_message,
            created_at=now_str,
            updated_at=now_str,
            is_complete=is_complete,
        )

        await self.session_repo.save(session)
        return IntakeSessionOutputDTO.from_entity(session)
