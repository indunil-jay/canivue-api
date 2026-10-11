from app.features.assessments.domain.entities import (
    AssessmentResult,
    DogFacts,
    FusionEngineProtocol,
    FusionInput,
    FusionOutput,
    ModalityResult,
    ProgressionOutput,
    RiskFactor,
    RiskLevel,
)

HORIZON_DAYS = 7

# (keywords, suspected condition, category, baseline severity). The first match wins.
_CONDITION_RULES: list[tuple[tuple[str, ...], str, str, float]] = [
    (("ear", "shaking head", "head shaking"), "Suspected Ear Infection", "Ear", 70),
    (
        ("itch", "scratch", "rash", "red skin", "redness", "hair loss", "bald"),
        "Suspected Skin Infection",
        "Skin",
        72,
    ),
    (("limp", "joint", "stiff", "won't walk", "leg"), "Suspected Joint Strain", "Joint", 60),
    (
        ("vomit", "diarrhea", "diarrhoea", "not eating", "appetite"),
        "Suspected Digestive Upset",
        "Digestive",
        58,
    ),
    (
        ("cough", "sneeze", "breath", "wheeze", "nose"),
        "Suspected Respiratory Concern",
        "Respiratory",
        62,
    ),
    (
        ("lethargic", "tired", "low energy", "sleeping a lot"),
        "Suspected Systemic Infection",
        "Systemic",
        65,
    ),
    (
        ("wound", "bleeding", "cut", "swelling", "swollen"),
        "Suspected Wound / Inflammation",
        "Wound",
        74,
    ),
]
_WELLNESS = ("General Wellness Check", "General", 30.0)

# (label, weight). Weights are renormalised over the factors that are available.
_W_SEVERITY, _W_TREND, _W_PROGRESSION, _W_BREED, _W_HISTORY, _W_AGE = 30, 20, 25, 10, 5, 10


def _breed_risk(breed: str) -> float:
    b = breed.lower()
    if "bulldog" in b or "pug" in b:
        return 75
    if "retriever" in b or "labrador" in b:
        return 68
    if "shepherd" in b:
        return 60
    if "poodle" in b or "terrier" in b:
        return 55
    return 48


def _age_risk(age_years: int) -> float:
    if age_years >= 8:
        return 78
    if age_years >= 5:
        return 58
    if age_years <= 1:
        return 42
    return 32


def _history_risk(dog: DogFacts) -> float:
    score = 35.0
    if any(a.strip() and "none" not in a.lower() for a in dog.allergies):
        score += 25
    notes = dog.special_notes.lower()
    if any(word in notes for word in ("recur", "sensitive", "chronic")):
        score += 20
    return min(score, 100.0)


class StubFusionEngine(FusionEngineProtocol):
    """Deterministic stand-in for the trained fusion and progression models.

    It reproduces the confidence-weighted fusion and weighted progression arithmetic, but the
    per-modality confidence figures are rule-based: there is no vision or sensor model here,
    so a photo and collar data are credited as evidence without being interpreted.
    """

    version = "stub-fusion-v1"

    async def assess(self, evidence: FusionInput) -> AssessmentResult:
        text = (evidence.symptoms.text if evidence.symptoms else "").lower()
        condition, category, severity = _WELLNESS
        for keywords, label, rule_category, rule_severity in _CONDITION_RULES:
            if any(k in text for k in keywords):
                condition, category, severity = label, rule_category, rule_severity
                break
        matched = condition != _WELLNESS[0]
        worsening = bool(evidence.symptoms and evidence.symptoms.worsening)

        # (name, available, confidence, quality)
        streams = [
            ("Image", evidence.has_image, 92 if matched else 74, 88),
            (
                "Smart Collar",
                evidence.sensors is not None,
                85 if matched else 66,
                min(100, 40 + 3 * evidence.sensors.reading_count) if evidence.sensors else 0,
            ),
            (
                "Symptom Text",
                evidence.symptoms is not None,
                round(evidence.symptoms.confidence * 100) if evidence.symptoms else 0,
                round(evidence.symptoms.quality * 100) if evidence.symptoms else 0,
            ),
        ]
        reliabilities = [conf * quality / 100 if ok else 0 for _, ok, conf, quality in streams]
        total = sum(reliabilities)
        modalities, final_confidence = [], 0.0
        for (name, ok, conf, quality), reliability in zip(streams, reliabilities, strict=True):
            share = reliability / total * 100 if ok and total > 0 else 0.0
            final_confidence += share / 100 * conf
            modalities.append(
                ModalityResult(
                    name=name,
                    available=ok,
                    confidence_percent=float(conf if ok else 0),
                    quality_percent=float(quality if ok else 0),
                    contribution_percent=round(share, 1),
                )
            )

        notes = []
        if not evidence.has_image:
            notes.append("Image was unavailable — the result relies on the remaining inputs.")
        if evidence.sensors is None:
            notes.append(
                "Smart-collar data was unavailable — the result relies on the remaining inputs."
            )
        if evidence.symptoms is None:
            notes.append("No symptom description was provided.")

        fusion = FusionOutput(
            condition=condition,
            category=category,
            final_confidence_percent=round(final_confidence, 1),
            severity_label=(
                "Moderate–Severe" if severity >= 70 else "Moderate" if severity >= 50 else "Mild"
            ),
            modalities=modalities,
            notes=notes,
        )
        return AssessmentResult(
            fusion=fusion,
            progression=self._progression(evidence, severity, matched, worsening),
            model_version=self.version,
        )

    def _progression(
        self, evidence: FusionInput, severity: float, matched: bool, worsening: bool
    ) -> ProgressionOutput:
        symptom_progression = (82.0 if worsening else 45.0) if matched else 20.0
        scored = [
            ("Current disease severity", severity, _W_SEVERITY),
            ("Symptom progression", symptom_progression, _W_PROGRESSION),
            ("Breed-related risk", _breed_risk(evidence.dog.breed), _W_BREED),
            ("Medical history", _history_risk(evidence.dog), _W_HISTORY),
            ("Age-related risk", _age_risk(evidence.dog.age_years), _W_AGE),
        ]
        if evidence.sensors is not None:
            trend = 30 + 60 * evidence.sensors.abnormal_fraction
            scored.append(("Behavioural trend (collar)", trend, _W_TREND))

        total_weight = sum(weight for _, _, weight in scored)
        factors = sorted(
            (
                RiskFactor(
                    label=label,
                    score_percent=round(score, 1),
                    weight_percent=round(weight / total_weight * 100, 1),
                    contribution_points=round(score * weight / total_weight, 1),
                )
                for label, score, weight in scored
            ),
            key=lambda f: f.contribution_points,
            reverse=True,
        )
        risk = sum(score * weight / total_weight for _, score, weight in scored)
        level = RiskLevel.from_score(risk)
        reasons = [f.label for f in factors[:3]]
        recommendation = level.recommendation

        emergency = evidence.symptoms.emergency_reason if evidence.symptoms else None
        if emergency:
            # A life-threatening cue in the owner's words overrides the arithmetic.
            risk, level = max(risk, 85.0), RiskLevel.CRITICAL
            reasons = [emergency, *reasons[:2]]
            recommendation = (
                evidence.symptoms.emergency_recommendation or RiskLevel.CRITICAL.recommendation
            )

        return ProgressionOutput(
            horizon_days=HORIZON_DAYS,
            risk_percent=round(risk, 1),
            risk_level=level,
            factors=factors,
            main_reasons=reasons,
            recommendation=recommendation,
            missing_data_note=(
                None
                if evidence.sensors is not None
                else "Behavioural-trend data was unavailable. The progression risk was "
                "recalculated using the remaining factors."
            ),
        )
