from __future__ import annotations

from app.features.symptom_nlp.domain.value_objects.symptom_parse_result import SymptomParseResult


def evaluate_missing_slots(parse_result: SymptomParseResult) -> list[str]:
    missing: list[str] = []

    # 1. Symptom presence
    if not parse_result.symptoms and not parse_result.negated_symptoms:
        missing.append("symptoms")

    # 2. Laterality check for bilateral anatomical locations
    bilateral_parts = {"ear", "eye", "paw", "leg", "nostril", "flank"}
    for loc in parse_result.body_locations:
        if (
            loc.part.lower() in bilateral_parts
            and not loc.side
            and "body_location_side" not in missing
        ):
            missing.append("body_location_side")

    # 3. Duration / Timeline
    if parse_result.duration is None:
        missing.append("duration")

    # 4. Progression / Severity trajectory
    if parse_result.progression is None and not parse_result.severity_cues:
        missing.append("progression")

    return missing
