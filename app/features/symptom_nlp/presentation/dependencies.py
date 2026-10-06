from pathlib import Path

from fastapi import Depends

from app.config import settings
from app.features.symptom_nlp.application.use_cases import (
    CompleteIntakeSessionUseCase,
    ConductIntakeTurnUseCase,
    ParseSymptomTextUseCase,
    StartIntakeSessionUseCase,
)
from app.features.symptom_nlp.domain.repositories import (
    IntakeSessionRepositoryProtocol,
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


def get_parse_symptom_use_case(
    engine: NLPSymptomEngineProtocol = Depends(get_symptom_engine),
) -> ParseSymptomTextUseCase:
    return ParseSymptomTextUseCase(engine=engine)


def get_start_intake_use_case(
    engine: NLPSymptomEngineProtocol = Depends(get_symptom_engine),
    session_repo: IntakeSessionRepositoryProtocol = Depends(get_intake_session_repository),
) -> StartIntakeSessionUseCase:
    return StartIntakeSessionUseCase(engine=engine, session_repo=session_repo)


def get_conduct_intake_turn_use_case(
    engine: NLPSymptomEngineProtocol = Depends(get_symptom_engine),
    session_repo: IntakeSessionRepositoryProtocol = Depends(get_intake_session_repository),
) -> ConductIntakeTurnUseCase:
    return ConductIntakeTurnUseCase(engine=engine, session_repo=session_repo)


def get_complete_intake_session_use_case(
    session_repo: IntakeSessionRepositoryProtocol = Depends(get_intake_session_repository),
) -> CompleteIntakeSessionUseCase:
    return CompleteIntakeSessionUseCase(session_repo=session_repo)
