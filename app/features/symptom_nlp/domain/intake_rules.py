from __future__ import annotations

from app.features.symptom_nlp.domain.entities import SymptomParseResult


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


def generate_clarifying_prompt(
    parse_result: SymptomParseResult,
    missing_slots: list[str],
    turn_count: int,
) -> str:
    if parse_result.emergency_triage.is_critical:
        reason = parse_result.emergency_triage.reason or "acute life-threatening symptoms"
        recommendation = (
            parse_result.emergency_triage.recommendation
            or "Please take your dog to the nearest 24/7 veterinary emergency hospital immediately."
        )
        return (
            f"URGENT MEDICAL ALERT: The symptoms described involve {reason}. "
            f"Routine intake is halted. {recommendation}"
        )

    if turn_count >= 4:
        return (
            "Thank you for sharing this information. We have reached the consultation limit, "
            "and I have summarized the complete clinical findings for veterinary review."
        )

    if not missing_slots:
        return (
            "Thank you for providing these thorough details. I have captured the full clinical "
            "picture of your dog's symptoms. Would you like to finalize this assessment?"
        )

    # Prioritize question generation
    if "symptoms" in missing_slots:
        return (
            "Thank you for reaching out. Could you describe the specific physical signs "
            "or changes in behavior you are observing in your dog?"
        )

    if "body_location_side" in missing_slots and "duration" in missing_slots:
        sym_desc = ", ".join(s.replace("_", " ") for s in parse_result.symptoms) or "these symptoms"
        return (
            f"I understand your dog is experiencing {sym_desc}. To help assess this accurately: "
            "which side is affected (left, right, or both), and how long has this been going on?"
        )

    if "body_location_side" in missing_slots:
        parts = [loc.part for loc in parse_result.body_locations if not loc.side]
        part_name = parts[0] if parts else "affected area"
        return (
            f"Could you clarify which side of the {part_name} is affected (left, right, or both)?"
        )

    if "duration" in missing_slots:
        return "Approximately how long has your dog been showing these signs (e.g. since yesterday, 3 days, 2 weeks)?"

    if "progression" in missing_slots:
        return "Are these symptoms getting worse, improving, or staying about the same?"

    return "Thank you for the update. Is there anything else you have observed about your dog?"
