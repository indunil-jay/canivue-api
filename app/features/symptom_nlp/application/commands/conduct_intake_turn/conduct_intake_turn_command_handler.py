from datetime import datetime, timezone

from app.features.symptom_nlp.application.commands.conduct_intake_turn.conduct_intake_turn_command import (
    ConductIntakeTurnCommand,
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
from app.features.symptom_nlp.domain.exceptions import (
    EmptySymptomTextException,
    IntakeSessionClosedException,
    IntakeSessionNotFoundException,
)
from app.features.symptom_nlp.domain.services.evaluate_missing_slots import evaluate_missing_slots
from app.features.symptom_nlp.domain.services.generate_clarifying_prompt import (
    generate_clarifying_prompt,
)
from app.features.symptom_nlp.domain.value_objects.intake_message import IntakeMessage


class ConductIntakeTurnCommandHandler:
    def __init__(
        self,
        engine: NLPSymptomEngineProtocol,
        session_repo: IntakeSessionRepositoryProtocol,
    ):
        self.engine = engine
        self.session_repo = session_repo

    async def handle(self, command: ConductIntakeTurnCommand) -> IntakeSessionOutputDTO:
        clean_text = command.message.strip() if command.message else ""
        if not clean_text:
            raise EmptySymptomTextException()

        session = await self.session_repo.get(command.session_id)
        if session is None:
            raise IntakeSessionNotFoundException(
                message=f"Intake session '{command.session_id}' not found."
            )

        if session.status in {"completed", "emergency_diverted"}:
            raise IntakeSessionClosedException(
                message=f"Intake session is already {session.status}."
            )

        now_str = datetime.now(timezone.utc).isoformat()
        user_msg = IntakeMessage(role="user", content=clean_text, created_at=now_str)
        session.messages.append(user_msg)

        # Synthesize cumulative narrative across all user messages
        user_texts = [m.content for m in session.messages if m.role == "user"]
        combined_narrative = ". ".join(user_texts)

        # Parse updated cumulative clinical narrative
        parse_result = await self.engine.parse(combined_narrative)

        session.turn_count += 1
        missing_slots = evaluate_missing_slots(parse_result)
        agent_message = generate_clarifying_prompt(
            parse_result, missing_slots, turn_count=session.turn_count
        )

        agent_msg = IntakeMessage(role="agent", content=agent_message, created_at=now_str)
        session.messages.append(agent_msg)

        is_emergency = parse_result.emergency_triage.is_critical
        if is_emergency:
            session.status = "emergency_diverted"
            session.is_complete = True
        elif session.turn_count >= 4 or not missing_slots:
            session.is_complete = not bool(missing_slots)

        session.accumulated_parse = parse_result
        session.missing_slots = missing_slots
        session.agent_message = agent_message
        session.updated_at = now_str

        await self.session_repo.save(session)
        return IntakeSessionOutputDTO.from_entity(session)
