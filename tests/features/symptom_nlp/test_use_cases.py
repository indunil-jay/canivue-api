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


@pytest.mark.asyncio
async def test_emergency_triage_respiratory_and_collapse():
    engine = StubNLPSymptomEngine()
    use_case = ParseSymptomTextUseCase(engine=engine)

    text = "My dog collapsed and is struggling to breathe after walking outside."
    result = await use_case.execute(ParseSymptomInputDTO(text=text))

    assert result.emergency_triage.is_critical is True
    assert result.emergency_triage.reason is not None
    assert "emergency veterinary hospital" in (result.emergency_triage.recommendation or "").lower()


@pytest.mark.asyncio
async def test_emergency_triage_toxic_ingestion():
    engine = StubNLPSymptomEngine()
    use_case = ParseSymptomTextUseCase(engine=engine)

    text = "He ate chocolate and rat poison an hour ago."
    result = await use_case.execute(ParseSymptomInputDTO(text=text))

    assert result.emergency_triage.is_critical is True
    assert "toxic" in (result.emergency_triage.reason or "").lower()


@pytest.mark.asyncio
async def test_emergency_triage_neurological_seizure():
    engine = StubNLPSymptomEngine()
    use_case = ParseSymptomTextUseCase(engine=engine)

    text = "She had a sudden seizure and was convulsing."
    result = await use_case.execute(ParseSymptomInputDTO(text=text))

    assert result.emergency_triage.is_critical is True
    assert "seizure" in (result.emergency_triage.reason or "").lower()


@pytest.mark.asyncio
async def test_safe_non_emergency_text():
    engine = StubNLPSymptomEngine()
    use_case = ParseSymptomTextUseCase(engine=engine)

    text = "Dog has mild itching on back for 2 days."
    result = await use_case.execute(ParseSymptomInputDTO(text=text))

    assert result.emergency_triage.is_critical is False
    assert result.emergency_triage.reason is None
    assert result.emergency_triage.recommendation is None


@pytest.mark.asyncio
async def test_negation_scoping_mixed_symptoms():
    engine = StubNLPSymptomEngine()
    use_case = ParseSymptomTextUseCase(engine=engine)

    text = "Dog has redness and scratching on his ear, but no vomiting and no coughing."
    result = await use_case.execute(ParseSymptomInputDTO(text=text))

    assert "scratching" in result.symptoms
    assert "redness" in result.symptoms
    assert "vomiting" in result.negated_symptoms
    assert "coughing" in result.negated_symptoms
    assert "vomiting" not in result.symptoms
    assert "coughing" not in result.symptoms

    # Check span negation attribute
    vomit_spans = [s for s in result.spans if s.text == "vomiting"]
    assert len(vomit_spans) > 0
    assert vomit_spans[0].negated is True


@pytest.mark.asyncio
async def test_temporal_duration_relative_and_units():
    engine = StubNLPSymptomEngine()
    use_case = ParseSymptomTextUseCase(engine=engine)

    text = "Discharge from left eye since this morning, getting worse."
    result = await use_case.execute(ParseSymptomInputDTO(text=text))

    assert result.duration is not None
    assert result.duration.value == 6
    assert result.duration.unit == "hours"
    assert result.progression == "worsening"


@pytest.mark.asyncio
async def test_frequency_mapping_constant_and_spans():
    engine = StubNLPSymptomEngine()
    use_case = ParseSymptomTextUseCase(engine=engine)

    text = "He is scratching ears constantly for 4 days."
    result = await use_case.execute(ParseSymptomInputDTO(text=text))

    assert result.frequency is not None
    assert result.frequency.get("descriptor") == "constant"

    # Verify all span character offsets match raw text
    for span in result.spans:
        assert text[span.start:span.end] == span.text


@pytest.mark.asyncio
async def test_missing_duration_returns_none_without_fabrication():
    engine = StubNLPSymptomEngine()
    use_case = ParseSymptomTextUseCase(engine=engine)

    text = "Redness and swelling on paw."
    result = await use_case.execute(ParseSymptomInputDTO(text=text))

    assert result.duration is None
    assert "DURATION_NOT_PROVIDED" in result.warnings
