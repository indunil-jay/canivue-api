"""Runtime inference pipeline for Multi-Task Canine Symptom NLP.

Loads trained model weights from model_registry/nlp/, runs multi-task token
extraction and condition classification, and applies deterministic clinical
safety guardrails (emergency triage, negation scoping, temporal duration normalization).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.features.symptom_nlp.infrastructure.ml.engine import (
    BODY_PARTS,
    DURATION_PATTERNS,
    FREQUENCY_PATTERNS,
    SIDES,
    SYMPTOM_LEXICON,
    WORD_TO_NUM,
)
from app.features.symptom_nlp.infrastructure.ml.preprocessing import (
    calculate_modality_reliability,
    calculate_text_quality_score,
    check_emergency_triage,
)
from ml.nlp.dataset import (
    CONDITION_LABELS,
    ID2LABEL,
)


class SymptomParserPipeline:
    """Production runtime inference pipeline for canine symptom parsing."""

    def __init__(
        self,
        checkpoint_path: str | Path | None = None,
        device: str | None = None,
    ):
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self.device = device
        self.model = None
        self.tokenizer = None
        self.model_version = "symptom_distilbert_v1"
        self._is_fallback = True

        if self.checkpoint_path and self.checkpoint_path.exists():
            self._load_model()
        else:
            # Fallback heuristic mode when checkpoint is not yet generated
            self._is_fallback = True
            self.model_version = (
                self.checkpoint_path.name if self.checkpoint_path else "symptom_fallback_v1"
            )

    def _load_model(self) -> None:
        """Load tokenizer and trained multi-task transformer checkpoint."""
        try:
            import torch
            from transformers import AutoTokenizer

            from ml.nlp.model import MultiTaskSymptomTransformer

            if self.device is None:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"

            self.tokenizer = AutoTokenizer.from_pretrained(str(self.checkpoint_path))
            self.model = MultiTaskSymptomTransformer.from_pretrained(self.checkpoint_path)
            self.model.to(self.device)
            self.model.eval()
            self._is_fallback = False
            self.model_version = self.checkpoint_path.name or "symptom_distilbert_v1"
        except (ImportError, OSError, RuntimeError, ValueError):
            # Fallback gracefully if weights cannot be loaded or torch is missing
            self._is_fallback = True
            self.model_version = (
                self.checkpoint_path.name if self.checkpoint_path else "symptom_fallback_v1"
            )

    def predict(self, text: str) -> dict[str, Any]:
        """Execute end-to-end symptom parsing, triage checks, and condition prediction."""
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        normalized_lower = text.lower()
        emergency_alert = check_emergency_triage(text)

        # 1. Neural or Rule-based Entity Extraction & Probabilities
        if not self._is_fallback and self.model is not None and self.tokenizer is not None:
            spans, condition_probs, raw_confidence = self._neural_predict(text)
        else:
            spans, condition_probs, raw_confidence = self._heuristic_predict(text)

        # 2. Extract structured entities from spans and text
        symptoms: list[str] = []
        negated_symptoms: list[str] = []
        body_locations: list[dict[str, Any]] = []
        behaviours: list[str] = []
        severity_cues: list[str] = []
        new_symptoms: list[str] = []

        for span in spans:
            ent = span["entity"]
            val = span["text"].lower()

            if ent == "symptom":
                # Standardize symptom name using lexicon if possible
                std_name = SYMPTOM_LEXICON.get(val, (val, "other"))[0]
                if span.get("negated", False):
                    if std_name not in negated_symptoms:
                        negated_symptoms.append(std_name)
                else:
                    if std_name not in symptoms:
                        symptoms.append(std_name)
                if (
                    std_name in {"scratching", "head_shaking", "limping", "reduced_activity"}
                    and std_name not in behaviours
                    and not span.get("negated", False)
                ):
                    behaviours.append(std_name)

            elif ent == "body_location":
                # Determine laterality if present
                side = None
                for s in SIDES:
                    if s in val:
                        side = s
                        break
                part = val.replace("left", "").replace("right", "").replace("both", "").strip()
                part = part.rstrip("s")
                body_locations.append({"part": part or val, "side": side})

            elif ent == "severity":
                severity_cues.append(val)

        # 3. Temporal Duration Extraction
        duration_dict: dict[str, Any] | None = None
        for pattern, kind, default_val, unit in DURATION_PATTERNS:
            match = re.search(pattern, normalized_lower)
            if match:
                if kind == "num":
                    val_str = match.group(1).lower()
                    val = WORD_TO_NUM.get(val_str, int(val_str) if val_str.isdigit() else 1)
                    duration_dict = {"value": val, "unit": unit}
                else:
                    duration_dict = {"value": default_val, "unit": unit}
                if not any(s["entity"] == "duration" for s in spans):
                    spans.append(
                        {
                            "entity": "duration",
                            "text": text[match.start() : match.end()],
                            "start": match.start(),
                            "end": match.end(),
                            "negated": False,
                        }
                    )
                break

        # 4. Frequency Extraction
        frequency_dict: dict[str, str] | None = None
        for pattern, descriptor, rate in FREQUENCY_PATTERNS:
            match = re.search(pattern, normalized_lower)
            if match:
                frequency_dict = {
                    "descriptor": descriptor,
                    "frequency_rate": rate,
                }
                if not any(s["entity"] == "frequency" for s in spans):
                    spans.append(
                        {
                            "entity": "frequency",
                            "text": text[match.start() : match.end()],
                            "start": match.start(),
                            "end": match.end(),
                            "negated": False,
                        }
                    )
                break

        # 5. Progression Trajectory
        progression: str | None = None
        if re.search(r"\b(getting worse|worse|worsening|increasing|spreading)\b", normalized_lower):
            progression = "worsening"
            severity_cues.append("getting_worse")
        elif re.search(r"\b(getting better|improving|less frequent|reduced)\b", normalized_lower):
            progression = "improving"
            severity_cues.append("improving")
        elif re.search(r"\b(unchanged|same as before|no change|stable)\b", normalized_lower):
            progression = "stable"

        if re.search(r"\b(becoming red|getting red)\b", normalized_lower):
            severity_cues.append("becoming_red")
            if "redness" not in new_symptoms and "redness" in symptoms:
                new_symptoms.append("redness")

        # 6. Quality & Confidence Scores
        has_symptom = len(symptoms) > 0
        has_loc = len(body_locations) > 0
        has_dur = duration_dict is not None
        has_sev_prog = bool(severity_cues or progression)

        quality_score = calculate_text_quality_score(
            text, has_symptom, has_loc, has_dur, has_sev_prog
        )
        model_confidence = raw_confidence if raw_confidence > 0.0 else (0.85 if has_symptom else 0.30)
        reliability_score = calculate_modality_reliability(quality_score, model_confidence)

        warnings: list[str] = []
        if not has_symptom:
            warnings.append("INSUFFICIENT_SYMPTOM_INFORMATION")
        if not has_dur:
            warnings.append("DURATION_NOT_PROVIDED")

        # Sort spans by character start offset
        spans.sort(key=lambda s: s["start"])

        return {
            "raw_text": text,
            "symptoms": symptoms,
            "negated_symptoms": negated_symptoms,
            "body_locations": body_locations,
            "duration": duration_dict,
            "frequency": frequency_dict,
            "severity_cues": severity_cues,
            "new_symptoms": new_symptoms,
            "progression": progression,
            "behaviours": behaviours,
            "condition_probabilities": condition_probs,
            "spans": spans,
            "text_quality_score": quality_score,
            "model_confidence": model_confidence,
            "modality_reliability_score": reliability_score,
            "emergency_triage": {
                "is_critical": emergency_alert.is_critical,
                "reason": emergency_alert.reason,
                "recommendation": emergency_alert.recommendation,
            },
            "warnings": warnings,
            "model_version": self.model_version,
        }

    def predict_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """Run batch inference on multiple texts."""
        return [self.predict(t) for t in texts]

    def _neural_predict(
        self, text: str
    ) -> tuple[list[dict[str, Any]], dict[str, float], float]:
        """Execute neural inference with Transformer model."""
        import torch

        inputs = self.tokenizer(
            text,
            return_offsets_mapping=True,
            return_tensors="pt",
            truncation=True,
            max_length=256,
        )
        offset_mapping = inputs.pop("offset_mapping")[0].tolist()
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(
                input_ids=inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
            )

        ner_logits = outputs["ner_logits"][0]  # [seq_len, num_ner_labels]
        condition_logits = outputs["condition_logits"][0]  # [num_conditions]

        # Condition Softmax
        cond_probs_tensor = torch.softmax(condition_logits, dim=-1).cpu().tolist()
        condition_probs = {
            lbl: round(float(p), 4) for lbl, p in zip(CONDITION_LABELS, cond_probs_tensor)
        }
        max_cond_confidence = max(condition_probs.values())

        # NER BIO Decoding
        pred_label_ids = torch.argmax(ner_logits, dim=-1).cpu().tolist()
        spans: list[dict[str, Any]] = []

        current_entity: str | None = None
        current_start: int = 0
        current_end: int = 0

        for token_idx, (token_start, token_end) in enumerate(offset_mapping):
            if token_start == token_end:
                continue  # Special token

            tag = ID2LABEL.get(pred_label_ids[token_idx], "O")

            if tag.startswith("B-"):
                if current_entity is not None:
                    spans.append(
                        self._create_span_dict(text, current_entity, current_start, current_end)
                    )
                current_entity = tag[2:]
                current_start = token_start
                current_end = token_end
            elif tag.startswith("I-") and current_entity == tag[2:]:
                current_end = token_end
            else:
                if current_entity is not None:
                    spans.append(
                        self._create_span_dict(text, current_entity, current_start, current_end)
                    )
                    current_entity = None

        if current_entity is not None:
            spans.append(self._create_span_dict(text, current_entity, current_start, current_end))

        return spans, condition_probs, max_cond_confidence

    def _create_span_dict(
        self, text: str, entity: str, start: int, end: int
    ) -> dict[str, Any]:
        """Construct a span dictionary with character slicing and negation checking."""
        span_text = text[start:end]
        is_negated = False
        if entity == "symptom":
            pre_window = text[max(0, start - 20) : start].lower()
            is_negated = bool(
                re.search(r"\b(no|not|stopped|no longer|without)\s*$", pre_window.strip())
            )

        return {
            "entity": entity,
            "text": span_text,
            "start": start,
            "end": end,
            "negated": is_negated,
        }

    def _heuristic_predict(
        self, text: str
    ) -> tuple[list[dict[str, Any]], dict[str, float], float]:
        """Fallback deterministic rule-based predictions."""
        normalized_lower = text.lower()
        spans: list[dict[str, Any]] = []
        condition_votes: dict[str, int] = {c: 0 for c in CONDITION_LABELS}

        for term, (std_name, condition_cat) in SYMPTOM_LEXICON.items():
            pattern = rf"\b{re.escape(term)}\b"
            for match in re.finditer(pattern, normalized_lower):
                start, end = match.start(), match.end()
                pre_window = normalized_lower[max(0, start - 20) : start]
                is_negated = bool(
                    re.search(r"\b(no|not|stopped|no longer|without)\s*$", pre_window.strip())
                )

                spans.append(
                    {
                        "entity": "symptom",
                        "text": text[start:end],
                        "start": start,
                        "end": end,
                        "negated": is_negated,
                    }
                )
                if not is_negated:
                    condition_votes[condition_cat] += 2

        for part in BODY_PARTS:
            for side in SIDES:
                loc_pattern = rf"\b{side}\s+{part}s?\b"
                for match in re.finditer(loc_pattern, normalized_lower):
                    spans.append(
                        {
                            "entity": "body_location",
                            "text": text[match.start() : match.end()],
                            "start": match.start(),
                            "end": match.end(),
                            "negated": False,
                        }
                    )
            isolated_pattern = rf"\b(the|its|his|her)?\s*{part}s?\b"
            for match in re.finditer(isolated_pattern, normalized_lower):
                if not any(
                    s["entity"] == "body_location"
                    and s["start"] <= match.start()
                    and s["end"] >= match.end()
                    for s in spans
                ):
                    spans.append(
                        {
                            "entity": "body_location",
                            "text": text[match.start() : match.end()],
                            "start": match.start(),
                            "end": match.end(),
                            "negated": False,
                        }
                    )

        total_votes = sum(condition_votes.values())
        if total_votes > 0:
            probs = {k: round(v / total_votes, 2) for k, v in condition_votes.items()}
            remainder = round(1.0 - sum(probs.values()), 2)
            probs["other"] = round(probs["other"] + remainder, 2)
        else:
            probs = {c: 0.25 for c in CONDITION_LABELS}

        confidence = 0.85 if total_votes > 0 else 0.30
        return spans, probs, confidence
