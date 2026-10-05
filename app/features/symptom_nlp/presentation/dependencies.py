from fastapi import Depends

from app.features.symptom_nlp.application.use_cases import ParseSymptomTextUseCase
from app.features.symptom_nlp.domain.repositories import NLPSymptomEngineProtocol
from app.features.symptom_nlp.infrastructure.ml.engine import StubNLPSymptomEngine


def get_symptom_engine() -> NLPSymptomEngineProtocol:
    """Dependency provider for the NLP Symptom engine.
    
    Returns the deterministic StubNLPSymptomEngine by default.
    """
    return StubNLPSymptomEngine()


def get_parse_symptom_use_case(
    engine: NLPSymptomEngineProtocol = Depends(get_symptom_engine),
) -> ParseSymptomTextUseCase:
    """Dependency provider for ParseSymptomTextUseCase."""
    return ParseSymptomTextUseCase(engine=engine)
