import uuid
from datetime import datetime, timezone

from app.features.symptom_nlp.application.dtos import (
    ConductTurnInputDTO,
    IntakeSessionOutputDTO,
    ParseSymptomInputDTO,
    ParseSymptomOutputDTO,
    StartIntakeInputDTO,
)
from app.features.symptom_nlp.domain.entities import IntakeMessage, IntakeSession
from app.features.symptom_nlp.domain.exceptions import (
    EmptySymptomTextException,
    IntakeSessionClosedException,
    IntakeSessionNotFoundException,
)
from app.features.symptom_nlp.domain.intake_rules import (
    evaluate_missing_slots,
    generate_clarifying_prompt,
)
from app.features.symptom_nlp.domain.repositories import (
    IntakeSessionRepositoryProtocol,
    NLPSymptomEngineProtocol,
)


class ParseSymptomTextUseCase:
    """Use case coordinating symptom text validation and NLP engine parsing."""

    def __init__(self, engine: NLPSymptomEngineProtocol):
        self.engine = engine

    async def execute(self, input_dto: ParseSymptomInputDTO) -> ParseSymptomOutputDTO:
        clean_text = input_dto.text.strip() if input_dto.text else ""
        if not clean_text:
            raise EmptySymptomTextException()

        parse_result = await self.engine.parse(clean_text)
        return ParseSymptomOutputDTO.from_entity(parse_result)


class StartIntakeSessionUseCase:
    """Use case to initialize a multi-turn canine symptom intake session."""

    def __init__(
        self,
        engine: NLPSymptomEngineProtocol,
        session_repo: IntakeSessionRepositoryProtocol,
    ):
        self.engine = engine
        self.session_repo = session_repo

    async def execute(self, input_dto: StartIntakeInputDTO) -> IntakeSessionOutputDTO:
        clean_text = input_dto.initial_text.strip() if input_dto.initial_text else ""
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
            dog_id=input_dto.dog_id,
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


class ConductIntakeTurnUseCase:
    """Use case to conduct a follow-up consultation turn and accumulate clinical context."""

    def __init__(
        self,
        engine: NLPSymptomEngineProtocol,
        session_repo: IntakeSessionRepositoryProtocol,
    ):
        self.engine = engine
        self.session_repo = session_repo

    async def execute(self, input_dto: ConductTurnInputDTO) -> IntakeSessionOutputDTO:
        clean_text = input_dto.message.strip() if input_dto.message else ""
        if not clean_text:
            raise EmptySymptomTextException()

        session = await self.session_repo.get(input_dto.session_id)
        if session is None:
            raise IntakeSessionNotFoundException(
                message=f"Intake session '{input_dto.session_id}' not found."
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


class CompleteIntakeSessionUseCase:
    """Use case to finalize an intake consultation and export structured clinical evidence."""

    def __init__(self, session_repo: IntakeSessionRepositoryProtocol):
        self.session_repo = session_repo

    async def execute(self, session_id: str) -> ParseSymptomOutputDTO:
        session = await self.session_repo.get(session_id)
        if session is None:
            raise IntakeSessionNotFoundException(
                message=f"Intake session '{session_id}' not found."
            )

        session.status = "completed"
        session.is_complete = True
        session.updated_at = datetime.now(timezone.utc).isoformat()
        await self.session_repo.save(session)
        return ParseSymptomOutputDTO.from_entity(session.accumulated_parse)



