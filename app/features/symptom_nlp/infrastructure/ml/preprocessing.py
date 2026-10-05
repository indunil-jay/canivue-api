import re

from app.features.symptom_nlp.domain.entities import EmergencyTriageAlert

# Critical red-flag emergency keywords & patterns
EMERGENCY_RED_FLAGS: list[tuple[str, str]] = [
    (r"\b(collapse[ds]?|collapsed|passed out|unresponsive)\b", "Sudden collapse or loss of consciousness"),
    (r"\b(struggling to breathe|difficulty breathing|choking|gasping)\b", "Acute respiratory distress"),
    (r"\b(blue gums|purple gums|pale white gums)\b", "Severe hypoxia or cardiovascular shock"),
    (r"\b(seizures?|convulsing|convulsions?)\b", "Acute neurological seizure activity"),
    (r"\b(poison(ed|ing)?|ate chocolate|swallowed battery|rat poison|toxic)\b", "Suspected acute toxic ingestion"),
    (r"\b(heavy bleeding|arterial bleeding|hit by car)\b", "Severe acute trauma or hemorrhage"),
    (r"\b(distended abdomen|distended stomach|bloat(ed)?|dry heaving and bloated)\b", "Suspected acute gastric dilatation-volvulus (bloat)"),
]


def check_emergency_triage(text: str) -> EmergencyTriageAlert:
    """Scan text for acute life-threatening emergency cues."""
    normalized = text.lower()
    for pattern, reason in EMERGENCY_RED_FLAGS:
        if re.search(pattern, normalized):
            return EmergencyTriageAlert(
                is_critical=True,
                reason=reason,
                recommendation="Seek emergency veterinary hospital care immediately.",
            )
    return EmergencyTriageAlert(is_critical=False, reason=None, recommendation=None)


def calculate_text_quality_score(
    text: str,
    has_symptom: bool,
    has_location: bool,
    has_duration: bool,
    has_severity_or_progression: bool,
) -> float:
    """Calculate deterministic text quality score (0.0 to 1.0) according to project rubric.
    
    Rubric:
      - Symptom term presence: 0.30
      - Body location identified: 0.20
      - Duration identified: 0.20
      - Severity / progression cues: 0.15
      - Syntactic length / completeness (>= 8 words): 0.15
      - Hard cap: < 3 words or 0 symptoms caps at 0.10.
    """
    words = text.strip().split()
    word_count = len(words)

    if word_count < 3 or not has_symptom:
        return 0.10

    score = 0.0
    if has_symptom:
        score += 0.30
    if has_location:
        score += 0.20
    if has_duration:
        score += 0.20
    if has_severity_or_progression:
        score += 0.15
    if word_count >= 8:
        score += 0.15
    elif word_count >= 5:
        score += 0.08

    return round(min(1.0, score), 3)


def calculate_modality_reliability(quality: float, confidence: float) -> float:
    """Compute harmonic mean reliability weight for the Adaptive Multimodal Fusion Mechanism."""
    if quality <= 0.0 or confidence <= 0.0:
        return 0.0
    reliability = (2 * quality * confidence) / (quality + confidence)
    return round(reliability, 3)
