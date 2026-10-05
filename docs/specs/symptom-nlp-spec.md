# Spec: NLP Symptom Parser Module

**Status:** `completed`  
**Origin:** Multi-round interview synthesis via `grillme` & `grill-with-docs`  
**ADRs Referenced:** [ADR-0001](file:///C:/Users/indun/OneDrive/Desktop/canivue-api/docs/adr/0001-modular-monolith-clean-architecture.md), [ADR-0002](file:///C:/Users/indun/OneDrive/Desktop/canivue-api/docs/adr/0002-nlp-symptom-parser-architecture.md), [ADR-0003](file:///C:/Users/indun/OneDrive/Desktop/canivue-api/docs/adr/0003-clinical-safety-guardrails-and-negation.md)  
**Glossary:** [GLOSSARY.md](file:///C:/Users/indun/OneDrive/Desktop/canivue-api/GLOSSARY.md)

---

## Problem Statement

Dog owners describe pet illnesses using informal, ambiguous, and unstructured natural language (e.g. *"My dog has been scratching its left ear for three days and it is becoming red"*). The core multimodal clinical system—consisting of the Confidence-Weighted Adaptive Multimodal Fusion Mechanism and the Disease Progression and Risk Prediction Engine (DPRPE)—requires standardized, structured categorical features, normalized temporal quantities, and calibrated condition probabilities. 

Without an automated, clinically grounded NLP translation module, owner observations cannot be systematically weighted alongside sensor data or image analysis, risking missed diagnostic cues or misinterpretation of negated and emergency symptoms.

---

## Solution

A high-performance, multi-task NLP symptom parsing and classification pipeline. The module translates freeform text into structured symptom entities (symptoms, body locations with laterality, normalized durations, frequencies, severity cues, progression status, and behaviours), calculates calibrated probabilities across 4 canonical condition categories, reports independent text-quality and model-confidence scores, tags negated symptoms to prevent false positives, and triggers an emergency triage guardrail for life-threatening conditions.

Core model architectures and training logic are isolated in the offline ML workspace (`ml/nlp/`), while runtime serving is encapsulated in an inward-facing Clean Architecture feature (`app/features/symptom_nlp/`) behind an inference protocol with zero-dependency testing stubs.

---

## User Stories

1. As a dog owner, I want to describe my dog's symptoms in plain, natural language, so that I do not need medical jargon to seek health guidance.
2. As the Adaptive Multimodal Fusion Mechanism, I want structured condition probabilities for ear inflammation, skin condition, eye condition, and other conditions, so that I can combine text evidence with vision and sensor modalities.
3. As the Adaptive Multimodal Fusion Mechanism, I want a separate `text_quality_score` and `model_confidence`, so that I can compute the reliability weight of the text evidence stream.
4. As the Disease Progression and Risk Prediction Engine (DPRPE), I want structured duration (`{value, unit}`), progression trajectory (`worsening`/`improving`/`stable`), and new symptom alerts, so that I can model longitudinal disease risk.
5. As a veterinarian reviewing a case in the clinic portal, I want exact character spans of extracted entities highlighted on the owner's original text, so that I can verify the AI's interpretation at a glance.
6. As a veterinarian, I want negated symptoms (e.g. "no vomiting", "stopped scratching") to be explicitly captured as absent history rather than counted as active complaints, so that differential diagnosis is not biased.
7. As a dog owner whose pet is in acute distress, I want immediate emergency warnings when life-threatening symptoms (e.g. collapse, blue gums, respiratory distress) are mentioned, so that I seek immediate emergency clinical intervention.
8. As a backend developer, I want the web API and test suite to run quickly on CPU without requiring GPU drivers or multi-gigabyte PyTorch weight downloads by default, so that development and CI remain rapid.
9. As an ML engineer, I want reproducible training scripts with dog-level splitting in `ml/nlp/`, so that model evaluation prevents data leakage across multiple entries from the same animal.
10. As a clinical auditor, I want every parsed symptom response to record the model version identifier, so that predictions satisfy medical traceability standards (FR-16).
11. As an API client, I want structured warning codes when an owner's text is too short, nonsensical, or lacks symptoms, so that the client application can prompt the owner for more details.

---

## Implementation Decisions

### 1. Architectural Boundaries & Code Layout
- **Offline ML Pipeline (`ml/nlp/`)**:
  - Implements `MultiTaskSymptomTransformer` using `distilbert-base-uncased` with token-classification (BIO NER) and sequence-classification heads.
  - Implements deterministic post-processors for temporal extraction, frequency mapping, and rule-based text quality scoring.
  - Implements `SymptomParserPipeline` in `ml/nlp/pipeline.py` providing `.parse(text)` and `.batch_parse(texts)` for standalone execution.
  - Implements `dataset.py` with dog-level train/val/test splitting, `train.py` with joint multi-task loss weighting ($\alpha=0.6, \beta=0.4$), `evaluate.py` with Macro-F1 and ECE, and `seed_data.py` for immediate validation.
- **Serving Layer (`app/features/symptom_nlp/`)**:
  - `domain/`: Pure business entities (`SymptomParseResult`, `ConditionProbability`, `ExtractedSpan`, `DurationEntity`, `EmergencyTriageAlert`) and `NLPSymptomEngineProtocol`. Zero external framework dependencies.
  - `application/`: `ParseSymptomTextUseCase` coordinating input validation, inference, and response assembly.
  - `infrastructure/ml/engine.py`: `StubNLPSymptomEngine` (deterministic heuristic rules for instant tests/CI) and `TrainedNLPSymptomEngine` (delegates to `SymptomParserPipeline`).
  - `infrastructure/ml/preprocessing.py`: Emergency red-flag keyword interceptor, input length validation, and text quality scoring.
  - `presentation/`: FastAPI router exposing `POST /api/v1/symptoms/parse`.
- **Model Registry (`model_registry/nlp/`)**:
  - Checkpoint storage for versioned checkpoints (`model_registry/nlp/symptom_distilbert_v1/`). Binaries remain gitignored.

### 2. Contract Schemas & Data Shapes

#### Request Body:
```json
{
  "text": "My dog has been scratching its left ear for three days and it is becoming red."
}
```

#### Response Body:
```json
{
  "success": true,
  "data": {
    "raw_text": "My dog has been scratching its left ear for three days and it is becoming red.",
    "symptoms": ["scratching", "redness"],
    "negated_symptoms": [],
    "body_locations": [
      {
        "part": "ear",
        "side": "left"
      }
    ],
    "duration": {
      "value": 3,
      "unit": "days"
    },
    "frequency": null,
    "severity_cues": ["becoming_red"],
    "new_symptoms": ["redness"],
    "progression": "worsening",
    "behaviours": ["scratching"],
    "condition_probabilities": {
      "ear_inflammation": 0.82,
      "skin_condition": 0.11,
      "eye_condition": 0.02,
      "other": 0.05
    },
    "spans": [
      {
        "entity": "symptom",
        "text": "scratching",
        "start": 16,
        "end": 26,
        "negated": false
      },
      {
        "entity": "body_location",
        "text": "left ear",
        "start": 31,
        "end": 39,
        "negated": false
      }
    ],
    "text_quality_score": 0.88,
    "model_confidence": 0.85,
    "modality_reliability_score": 0.865,
    "emergency_triage": {
      "is_critical": false,
      "reason": null,
      "recommendation": null
    },
    "warnings": [],
    "model_version": "symptom_distilbert_v1"
  },
  "message": "Symptom text parsed successfully"
}
```

### 3. Text Quality & Reliability Scoring Formulas
- **Text Quality Score (0.0 to 1.0)**:
  - Symptom identified: 0.30
  - Body location identified: 0.20
  - Duration/timeline identified: 0.20
  - Severity or progression cue identified: 0.15
  - Minimum word count (>= 8 words) & syntactic structure: 0.15
  - *Hard Cap*: If recognized symptoms = 0 or word count < 3, `text_quality_score` capped at 0.10.
- **Modality Reliability Score (0.0 to 1.0)**:
  $$\text{Reliability} = \frac{2 \times \text{Quality} \times \text{Confidence}}{\text{Quality} + \text{Confidence}}$$

---

## Testing Decisions

### Seams Under Test
1. **Public Web API Seam (`POST /api/v1/symptoms/parse`)**:
   - Tested using `httpx.AsyncClient` against the FastAPI application router.
   - Verifies HTTP status codes, Pydantic request/response schema validation, error handling, emergency triage warnings, and response envelope consistency.
2. **Application Use Case Seam (`ParseSymptomTextUseCase.execute(dto)`)**:
   - Tested in pure Python with unit tests using `StubNLPSymptomEngine`.
   - Verifies domain entity transformations, negation handling, duration calculations, and warning generation without HTTP or database overhead.
3. **ML Preprocessing & Heuristics Seam (`ml/nlp/preprocessing.py`)**:
   - Tests emergency keyword detection (cyanosis, collapse, respiratory distress).
   - Tests text quality scoring calculation and boundary conditions (empty text, short text, comprehensive clinical paragraphs).

### Test Principles & What Makes a Good Test
- **Behavior-Driven**: Tests assert on observable clinical extractions and probabilities, never on internal Transformer weights or private class methods.
- **Independence**: Zero reliance on external GPU hardware or network calls to HuggingFace during test runs.

---

## Out of Scope

- Automated drug prescription or clinical treatment generation.
- Interactive multi-turn medical chat dialog (out of scope for this extraction engine).
- Non-English multilingual tokenization in the initial release.
- Image or audio processing (handled by vision and sensor feature modules).

---

## Further Notes

- Router registration: Register `symptom_nlp_router` in `app/main.py` under prefix `/api/v1/symptoms`.
- Downstream integration: The output schema directly matches the input signature required by the Confidence-Weighted Adaptive Multimodal Fusion Mechanism and DPRPE.
