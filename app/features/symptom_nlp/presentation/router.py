from fastapi import APIRouter, Depends, status

from app.core.response import APIResponse
from app.features.symptom_nlp.application.dtos import ParseSymptomInputDTO
from app.features.symptom_nlp.application.use_cases import ParseSymptomTextUseCase
from app.features.symptom_nlp.presentation.dependencies import get_parse_symptom_use_case
from app.features.symptom_nlp.presentation.schemas import (
    BodyLocationSchema,
    DurationSchema,
    EmergencyTriageSchema,
    ExtractedSpanSchema,
    SymptomParseRequest,
    SymptomParseResponseData,
)

router = APIRouter()


@router.post(
    "/parse",
    response_model=APIResponse[SymptomParseResponseData],
    status_code=status.HTTP_200_OK,
    summary="Parse informal symptom text into structured evidence",
    description=(
        "Translates freeform dog owner symptom text into normalized clinical features, "
        "calibrated condition probabilities, text-quality scores, and emergency triage alerts."
    ),
)
async def parse_symptoms(
    payload: SymptomParseRequest,
    use_case: ParseSymptomTextUseCase = Depends(get_parse_symptom_use_case),
) -> APIResponse[SymptomParseResponseData]:
    dto = ParseSymptomInputDTO(text=payload.text)
    result = await use_case.execute(dto)

    data = SymptomParseResponseData(
        raw_text=result.raw_text,
        symptoms=result.symptoms,
        negated_symptoms=result.negated_symptoms,
        body_locations=[
            BodyLocationSchema(part=loc.part, side=loc.side) for loc in result.body_locations
        ],
        duration=(
            DurationSchema(value=result.duration.value, unit=result.duration.unit)
            if result.duration
            else None
        ),
        frequency=result.frequency,
        severity_cues=result.severity_cues,
        new_symptoms=result.new_symptoms,
        progression=result.progression,
        behaviours=result.behaviours,
        condition_probabilities=result.condition_probabilities,
        spans=[
            ExtractedSpanSchema(
                entity=span.entity,
                text=span.text,
                start=span.start,
                end=span.end,
                negated=span.negated,
            )
            for span in result.spans
        ],
        text_quality_score=result.text_quality_score,
        model_confidence=result.model_confidence,
        modality_reliability_score=result.modality_reliability_score,
        emergency_triage=EmergencyTriageSchema(
            is_critical=result.emergency_triage.is_critical,
            reason=result.emergency_triage.reason,
            recommendation=result.emergency_triage.recommendation,
        ),
        warnings=result.warnings,
        model_version=result.model_version,
    )

    return APIResponse(
        success=True,
        message="Symptom text parsed successfully",
        data=data,
    )
