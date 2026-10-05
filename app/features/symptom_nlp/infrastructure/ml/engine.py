import re
from typing import Any

from app.features.symptom_nlp.domain.entities import (
    BodyLocation,
    DurationEntity,
    EmergencyTriageAlert,
    ExtractedSpan,
    SymptomParseResult,
)
from app.features.symptom_nlp.domain.repositories import NLPSymptomEngineProtocol
from app.features.symptom_nlp.infrastructure.ml.preprocessing import (
    calculate_modality_reliability,
    calculate_text_quality_score,
    check_emergency_triage,
)

# Symptom lexicon with condition mappings
SYMPTOM_LEXICON: dict[str, tuple[str, str]] = {
    # symptom_keyword: (standardized_name, condition_category)
    "scratching": ("scratching", "ear_inflammation"),
    "scratch": ("scratching", "ear_inflammation"),
    "head shaking": ("head_shaking", "ear_inflammation"),
    "shaking his head": ("head_shaking", "ear_inflammation"),
    "shaking her head": ("head_shaking", "ear_inflammation"),
    "shaking head": ("head_shaking", "ear_inflammation"),
    "ear canal": ("ear_canal", "ear_inflammation"),
    "redness": ("redness", "skin_condition"),
    "red": ("redness", "skin_condition"),
    "bad smell": ("bad_smell", "ear_inflammation"),
    "smells bad": ("bad_smell", "ear_inflammation"),
    "odor": ("bad_smell", "ear_inflammation"),
    "itching": ("itching", "skin_condition"),
    "itchy": ("itching", "skin_condition"),
    "hair loss": ("hair_loss", "skin_condition"),
    "losing hair": ("hair_loss", "skin_condition"),
    "bald patches": ("hair_loss", "skin_condition"),
    "swelling": ("swelling", "skin_condition"),
    "swollen": ("swelling", "skin_condition"),
    "discharge": ("discharge", "eye_condition"),
    "watery eyes": ("discharge", "eye_condition"),
    "watery eye": ("discharge", "eye_condition"),
    "cloudy eye": ("cloudy_eye", "eye_condition"),
    "cloudy film": ("cloudy_eye", "eye_condition"),
    "cloudy": ("cloudy_eye", "eye_condition"),
    "squinting": ("squinting", "eye_condition"),
    "limping": ("limping", "other"),
    "lethargic": ("lethargy", "other"),
    "reduced activity": ("reduced_activity", "other"),
    "coughing": ("coughing", "other"),
    "vomiting": ("vomiting", "other"),
    "diarrhea": ("diarrhea", "other"),
    "collapsed": ("collapse", "other"),
    "collapse": ("collapse", "other"),
    "struggling to breathe": ("dyspnea", "other"),
    "rapid breathing": ("dyspnea", "other"),
    "gasping": ("dyspnea", "other"),
    "blue gums": ("cyanosis", "other"),
    "pale blue": ("cyanosis", "other"),
    "seizures": ("seizures", "other"),
    "seizure": ("seizures", "other"),
    "unresponsive": ("unresponsive", "other"),
}

BODY_PARTS: list[str] = ["ear", "eye", "eyelid", "paw", "back", "abdomen", "skin", "belly", "leg", "tail", "mouth"]
SIDES: list[str] = ["left", "right", "both"]

DURATION_PATTERNS = [
    (r"\bsince this morning\b", "since_morning", 6, "hours"),
    (r"\bsince yesterday\b", "yesterday", 1, "days"),
    (r"\b(?:for\s+)?(?:a\s+)?couple(?:\s+of)?\s*(days?)\b", "couple_days", 2, "days"),
    (r"\b(?:for\s+)?(?:a\s+)?couple(?:\s+of)?\s*(weeks?)\b", "couple_weeks", 2, "weeks"),
    (r"\b(?:for\s+)?(?:a\s+)?week\b", "a_week", 1, "weeks"),
    (r"\b(?:for\s+)?several\s*(days?)\b", "several_days", 3, "days"),
    (r"\b(?:for\s+)?(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s*(days?)\b", "num", None, "days"),
    (r"\b(?:for\s+)?(one|two|three|four|five|six|\d+)\s*(weeks?)\b", "num", None, "weeks"),
    (r"\b(?:for\s+)?(one|two|three|four|five|six|\d+)\s*(months?)\b", "num", None, "months"),
    (r"\b(?:for\s+)?(one|two|three|four|five|six|eight|twelve|twenty-four|\d+)\s*(hours?)\b", "num", None, "hours"),
]

FREQUENCY_PATTERNS = [
    (r"\b(constantly|all day|non-stop|continuous(?:ly)?)\b", "constant", "high"),
    (r"\b(several times a day|multiple times daily|frequently|often)\b", "frequent", "moderate_high"),
    (r"\b(once a day|daily|every day)\b", "daily", "regular"),
    (r"\b(occasionally|intermittently|sometimes|now and then)\b", "intermittent", "low"),
]

WORD_TO_NUM = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "twelve": 12,
    "twenty-four": 24,
}


class StubNLPSymptomEngine(NLPSymptomEngineProtocol):
    """Deterministic, zero-dependency stub engine for NLP symptom parsing.
    
    Used for local testing, development mode, and CI without requiring PyTorch or GPUs.
    """

    def get_version(self) -> str:
        return "stub_nlp_engine_v1"

    async def parse(self, text: str) -> SymptomParseResult:
        normalized_lower = text.lower()
        emergency_alert = check_emergency_triage(text)

        symptoms: list[str] = []
        negated_symptoms: list[str] = []
        spans: list[ExtractedSpan] = []
        behaviours: list[str] = []
        severity_cues: list[str] = []
        new_symptoms: list[str] = []
        condition_votes: dict[str, int] = {
            "ear_inflammation": 0,
            "skin_condition": 0,
            "eye_condition": 0,
            "other": 0,
        }

        # 1. Extract Symptoms and BIO Spans
        for term, (std_name, condition_cat) in SYMPTOM_LEXICON.items():
            pattern = rf"\b{re.escape(term)}\b"
            for match in re.finditer(pattern, normalized_lower):
                start, end = match.start(), match.end()
                pre_window = normalized_lower[max(0, start - 20) : start]
                is_negated = bool(re.search(r"\b(no|not|stopped|no longer|without)\s*$", pre_window.strip()))

                span = ExtractedSpan(
                    entity="symptom",
                    text=text[start:end],
                    start=start,
                    end=end,
                    negated=is_negated,
                )
                spans.append(span)

                if is_negated:
                    if std_name not in negated_symptoms:
                        negated_symptoms.append(std_name)
                else:
                    if std_name not in symptoms:
                        symptoms.append(std_name)
                        condition_votes[condition_cat] += 2

                # Behaviour attribution
                if (
                    std_name in {"scratching", "head_shaking", "limping", "reduced_activity"}
                    and std_name not in behaviours
                    and not is_negated
                ):
                    behaviours.append(std_name)

        # 3. Extract Body Locations with Laterality
        body_locations: list[BodyLocation] = []
        for part in BODY_PARTS:
            for side in SIDES:
                loc_pattern = rf"\b{side}\s+{part}s?\b"
                for match in re.finditer(loc_pattern, normalized_lower):
                    start, end = match.start(), match.end()
                    body_locations.append(BodyLocation(part=part, side=side))
                    spans.append(ExtractedSpan(entity="body_location", text=text[start:end], start=start, end=end))
            
            # Isolated part without side
            isolated_pattern = rf"\b(the|its|his|her)?\s*{part}s?\b"
            for match in re.finditer(isolated_pattern, normalized_lower):
                if not any(loc.part == part for loc in body_locations):
                    body_locations.append(BodyLocation(part=part, side=None))
                    spans.append(ExtractedSpan(entity="body_location", text=text[match.start():match.end()], start=match.start(), end=match.end()))

        # 4. Extract Duration
        duration_entity: DurationEntity | None = None
        for pattern, kind, default_val, unit in DURATION_PATTERNS:
            match = re.search(pattern, normalized_lower)
            if match:
                if kind == "num":
                    val_str = match.group(1).lower()
                    val = WORD_TO_NUM.get(val_str, int(val_str) if val_str.isdigit() else 1)
                    duration_entity = DurationEntity(value=val, unit=unit)
                else:
                    duration_entity = DurationEntity(value=default_val, unit=unit)
                spans.append(
                    ExtractedSpan(
                        entity="duration",
                        text=text[match.start():match.end()],
                        start=match.start(),
                        end=match.end(),
                    )
                )
                break

        # 5. Extract Frequency
        frequency_dict: dict[str, str] | None = None
        for pattern, descriptor, rate in FREQUENCY_PATTERNS:
            match = re.search(pattern, normalized_lower)
            if match:
                frequency_dict = {
                    "descriptor": descriptor,
                    "frequency_rate": rate,
                }
                spans.append(
                    ExtractedSpan(
                        entity="frequency",
                        text=text[match.start():match.end()],
                        start=match.start(),
                        end=match.end(),
                    )
                )
                break

        # 6. Extract Progression & Severity Cues
        progression: str | None = None
        prog_match = re.search(
            r"\b(getting worse|worse|worsening|increasing|becoming redder|spreading)\b",
            normalized_lower,
        )
        if prog_match:
            progression = "worsening"
            severity_cues.append("getting_worse")
            spans.append(
                ExtractedSpan(
                    entity="progression",
                    text=text[prog_match.start():prog_match.end()],
                    start=prog_match.start(),
                    end=prog_match.end(),
                )
            )
        else:
            prog_match = re.search(
                r"\b(getting better|improving|less frequent|reduced)\b",
                normalized_lower,
            )
            if prog_match:
                progression = "improving"
                severity_cues.append("improving")
                spans.append(
                    ExtractedSpan(
                        entity="progression",
                        text=text[prog_match.start():prog_match.end()],
                        start=prog_match.start(),
                        end=prog_match.end(),
                    )
                )
            else:
                prog_match = re.search(
                    r"\b(unchanged|same as before|no change|stable)\b",
                    normalized_lower,
                )
                if prog_match:
                    progression = "stable"
                    spans.append(
                        ExtractedSpan(
                            entity="progression",
                            text=text[prog_match.start():prog_match.end()],
                            start=prog_match.start(),
                            end=prog_match.end(),
                        )
                    )

        if re.search(r"\b(becoming red|getting red)\b", normalized_lower):
            severity_cues.append("becoming_red")
            if "redness" not in new_symptoms and "redness" in symptoms:
                new_symptoms.append("redness")

        # 7. Calculate Condition Probabilities with Anatomical Context
        if emergency_alert.is_critical:
            condition_votes["other"] += 4

        if any(loc.part == "ear" for loc in body_locations):
            condition_votes["ear_inflammation"] += 3
        if any(loc.part in {"eye", "eyelid"} for loc in body_locations):
            condition_votes["eye_condition"] += 3
            if any(k in normalized_lower for k in ["around", "film", "discharge", "squinting"]):
                condition_votes["eye_condition"] += 2
        if any(loc.part in {"skin", "belly", "abdomen", "paw", "back"} for loc in body_locations):
            condition_votes["skin_condition"] += 2

        total_votes = sum(condition_votes.values())
        if total_votes > 0:
            probs = {k: round(v / total_votes, 2) for k, v in condition_votes.items()}
            # Normalize to sum exactly to 1.0
            remainder = round(1.0 - sum(probs.values()), 2)
            probs["other"] = round(probs["other"] + remainder, 2)
        else:
            probs = {
                "ear_inflammation": 0.0,
                "skin_condition": 0.0,
                "eye_condition": 0.0,
                "other": 1.0,
            }

        # 7. Quality & Confidence Scores
        has_symptom = len(symptoms) > 0
        has_loc = len(body_locations) > 0
        has_dur = duration_entity is not None
        has_sev_prog = bool(severity_cues or progression)

        quality_score = calculate_text_quality_score(text, has_symptom, has_loc, has_dur, has_sev_prog)
        model_confidence = 0.85 if has_symptom else 0.30
        reliability_score = calculate_modality_reliability(quality_score, model_confidence)

        warnings: list[str] = []
        if not has_symptom:
            warnings.append("INSUFFICIENT_SYMPTOM_INFORMATION")
        if not has_dur:
            warnings.append("DURATION_NOT_PROVIDED")

        return SymptomParseResult(
            raw_text=text,
            symptoms=symptoms,
            negated_symptoms=negated_symptoms,
            body_locations=body_locations,
            duration=duration_entity,
            frequency=frequency_dict,
            severity_cues=severity_cues,
            new_symptoms=new_symptoms,
            progression=progression,
            behaviours=behaviours,
            condition_probabilities=probs,
            spans=spans,
            text_quality_score=quality_score,
            model_confidence=model_confidence,
            modality_reliability_score=reliability_score,
            emergency_triage=emergency_alert,
            warnings=warnings,
            model_version=self.get_version(),
        )


class TrainedNLPSymptomEngine(NLPSymptomEngineProtocol):
    """Production Clean Architecture adapter wrapping SymptomParserPipeline.

    Loads model weights from model_registry/nlp/ and executes inference in a
    worker thread (asyncio.to_thread) to prevent blocking the FastAPI event loop.
    """

    def __init__(
        self,
        checkpoint_path: str | None = None,
        pipeline: Any = None,
    ):
        if pipeline is not None:
            self._pipeline = pipeline
        else:
            from ml.nlp.pipeline import SymptomParserPipeline

            self._pipeline = SymptomParserPipeline(checkpoint_path=checkpoint_path)

    def get_version(self) -> str:
        return getattr(self._pipeline, "model_version", "symptom_distilbert_v1")

    async def parse(self, text: str) -> SymptomParseResult:
        import asyncio

        res = await asyncio.to_thread(self._pipeline.predict, text)

        # Convert dictionary output to domain dataclass entities
        body_locations = [
            BodyLocation(part=loc["part"], side=loc.get("side"))
            for loc in res.get("body_locations", [])
        ]
        duration = None
        if res.get("duration"):
            duration = DurationEntity(
                value=res["duration"]["value"],
                unit=res["duration"]["unit"],
            )
        spans = [
            ExtractedSpan(
                entity=s["entity"],
                text=s["text"],
                start=s["start"],
                end=s["end"],
                negated=s.get("negated", False),
            )
            for s in res.get("spans", [])
        ]
        emergency_raw = res.get("emergency_triage", {})
        emergency = EmergencyTriageAlert(
            is_critical=emergency_raw.get("is_critical", False),
            reason=emergency_raw.get("reason"),
            recommendation=emergency_raw.get("recommendation"),
        )

        return SymptomParseResult(
            raw_text=res["raw_text"],
            symptoms=res.get("symptoms", []),
            negated_symptoms=res.get("negated_symptoms", []),
            body_locations=body_locations,
            duration=duration,
            frequency=res.get("frequency"),
            severity_cues=res.get("severity_cues", []),
            new_symptoms=res.get("new_symptoms", []),
            progression=res.get("progression"),
            behaviours=res.get("behaviours", []),
            condition_probabilities=res.get("condition_probabilities", {}),
            spans=spans,
            text_quality_score=res.get("text_quality_score", 0.0),
            model_confidence=res.get("model_confidence", 0.0),
            modality_reliability_score=res.get("modality_reliability_score", 0.0),
            emergency_triage=emergency,
            warnings=res.get("warnings", []),
            model_version=self.get_version(),
        )

