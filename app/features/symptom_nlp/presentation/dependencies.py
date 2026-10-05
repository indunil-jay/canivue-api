from pathlib import Path

from fastapi import Depends

from app.config import settings
from app.features.symptom_nlp.application.use_cases import ParseSymptomTextUseCase
from app.features.symptom_nlp.domain.repositories import NLPSymptomEngineProtocol
from app.features.symptom_nlp.infrastructure.ml.engine import (
    StubNLPSymptomEngine,
    TrainedNLPSymptomEngine,
)

_cached_engine: NLPSymptomEngineProtocol | None = None


def get_symptom_engine() -> NLPSymptomEngineProtocol:
    """Dependency provider for the NLP Symptom engine.
    
    Returns TrainedNLPSymptomEngine when USE_REAL_ML_MODELS is True and checkpoint exists,
    otherwise falls back to deterministic StubNLPSymptomEngine.
    """
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
    """Set or reset the cached symptom engine (used in tests and lifespan warmup)."""
    global _cached_engine
    _cached_engine = engine


def get_parse_symptom_use_case(
    engine: NLPSymptomEngineProtocol = Depends(get_symptom_engine),
) -> ParseSymptomTextUseCase:
    """Dependency provider for ParseSymptomTextUseCase."""
    return ParseSymptomTextUseCase(engine=engine)
