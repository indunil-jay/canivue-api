from pathlib import Path

from fastapi import Depends

from app.config import settings
from app.features.symptom_nlp.application.commands.complete_intake_session.complete_intake_session_command_handler import (
    CompleteIntakeSessionCommandHandler,
)
from app.features.symptom_nlp.application.commands.conduct_intake_turn.conduct_intake_turn_command_handler import (
    ConductIntakeTurnCommandHandler,
)
from app.features.symptom_nlp.application.commands.parse_symptom_text.parse_symptom_text_command_handler import (
    ParseSymptomTextCommandHandler,
)
from app.features.symptom_nlp.application.commands.start_intake_session.start_intake_session_command_handler import (
    StartIntakeSessionCommandHandler,
)
from app.features.symptom_nlp.application.interfaces.repositories.intake_session_repository import (
    IntakeSessionRepositoryProtocol,
)
from app.features.symptom_nlp.application.interfaces.services.nlp_symptom_engine import (
    NLPSymptomEngineProtocol,
)
from app.features.symptom_nlp.infrastructure.ml.engine import (
    StubNLPSymptomEngine,
    TrainedNLPSymptomEngine,
)
from app.features.symptom_nlp.infrastructure.persistence.repositories.session_repository import (
    InMemoryIntakeSessionRepository,
)

_cached_engine: NLPSymptomEngineProtocol | None = None
_session_repo: IntakeSessionRepositoryProtocol | None = None


def get_symptom_engine() -> NLPSymptomEngineProtocol:
    global _cached_engine
    if _cached_engine is not None:
        return _cached_engine

    if settings.USE_REAL_ML_MODELS:
        checkpoint_dir = Path(settings.MODEL_REGISTRY_DIR) / settings.NLP_MODEL_CHECKPOINT
        if checkpoint_dir.exists():
            _cached_engine = TrainedNLPSymptomEngine(checkpoint_path=str(checkpoint_dir))
            return _cached_engine

    return StubNLPSymptomEngine()


def set_symptom_engine_override(engine: NLPSymptomEngineProtocol | None) -> None:
    global _cached_engine
    _cached_engine = engine


def get_intake_session_repository() -> IntakeSessionRepositoryProtocol:
    global _session_repo
    if _session_repo is None:
        _session_repo = InMemoryIntakeSessionRepository()
    return _session_repo


def get_parse_symptom_text_command_handler(
    engine: NLPSymptomEngineProtocol = Depends(get_symptom_engine),
) -> ParseSymptomTextCommandHandler:
    return ParseSymptomTextCommandHandler(engine=engine)


def get_start_intake_session_command_handler(
    engine: NLPSymptomEngineProtocol = Depends(get_symptom_engine),
    session_repo: IntakeSessionRepositoryProtocol = Depends(get_intake_session_repository),
) -> StartIntakeSessionCommandHandler:
    return StartIntakeSessionCommandHandler(engine=engine, session_repo=session_repo)


def get_conduct_intake_turn_command_handler(
    engine: NLPSymptomEngineProtocol = Depends(get_symptom_engine),
    session_repo: IntakeSessionRepositoryProtocol = Depends(get_intake_session_repository),
) -> ConductIntakeTurnCommandHandler:
    return ConductIntakeTurnCommandHandler(engine=engine, session_repo=session_repo)


def get_complete_intake_session_command_handler(
    session_repo: IntakeSessionRepositoryProtocol = Depends(get_intake_session_repository),
) -> CompleteIntakeSessionCommandHandler:
    return CompleteIntakeSessionCommandHandler(session_repo=session_repo)
