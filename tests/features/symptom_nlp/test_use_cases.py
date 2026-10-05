import pytest

from app.features.symptom_nlp.application.dtos import ParseSymptomInputDTO
from app.features.symptom_nlp.application.use_cases import ParseSymptomTextUseCase
from app.features.symptom_nlp.domain.exceptions import EmptySymptomTextException
from app.features.symptom_nlp.infrastructure.ml.engine import StubNLPSymptomEngine


@pytest.mark.asyncio
async def test_parse_symptom_text_use_case_with_stub():
    engine = StubNLPSymptomEngine()
    use_case = ParseSymptomTextUseCase(engine=engine)

    sample_text = (
        "My dog has been scratching its left ear for three days and it is becoming red."
    )
    dto = ParseSymptomInputDTO(text=sample_text)
    result = await use_case.execute(dto)

    assert result.raw_text == sample_text
    assert "scratching" in result.symptoms
    assert any(loc.part == "ear" and loc.side == "left" for loc in result.body_locations)
    assert result.duration is not None
    assert result.duration.value == 3
    assert result.duration.unit == "days"
    assert "ear_inflammation" in result.condition_probabilities
    assert result.condition_probabilities["ear_inflammation"] > 0.5
    assert result.text_quality_score > 0.6
    assert result.model_confidence > 0.7
    assert result.modality_reliability_score > 0.6
    assert result.emergency_triage.is_critical is False
    assert result.model_version == "stub_nlp_engine_v1"


@pytest.mark.asyncio
async def test_empty_symptom_text_raises_exception():
    engine = StubNLPSymptomEngine()
    use_case = ParseSymptomTextUseCase(engine=engine)

    with pytest.raises(EmptySymptomTextException):
        await use_case.execute(ParseSymptomInputDTO(text="   "))
