# Spec: Conversational Clinical Intake Agent & Multi-Task Veterinary NLP Pipeline

**Status:** `completed`  
**Origin:** Synthesis of Wayfinder discovery and domain modeling  
**ADRs Referenced:** [ADR-0001](file:///c:/Users/indun/OneDrive/Desktop/canivue-api/docs/adr/0001-modular-monolith-clean-architecture.md), [ADR-0002](file:///c:/Users/indun/OneDrive/Desktop/canivue-api/docs/adr/0002-nlp-symptom-parser-architecture.md), [ADR-0003](file:///c:/Users/indun/OneDrive/Desktop/canivue-api/docs/adr/0003-clinical-safety-guardrails-and-negation.md)  
**Glossary:** [GLOSSARY.md](file:///c:/Users/indun/OneDrive/Desktop/canivue-api/GLOSSARY.md)  
**Wayfinder Map:** [map-canine-nlp-intake-agent.md](file:///c:/Users/indun/OneDrive/Desktop/canivue-api/docs/wayfinder/map-canine-nlp-intake-agent.md)

---

## Problem Statement

Dog owners describe pet illnesses using ambiguous, incomplete, and emotionally charged natural language. When an owner reports a vague symptom (such as *"My dog is scratching"* or *"Dog seems sick"*), a single-turn natural language parser cannot extract essential clinical features—such as duration, exact anatomical location and laterality, progression trajectory, or severity cues. Without these variables, the text quality score remains low, preventing downstream diagnostic systems (such as the Confidence-Weighted Adaptive Multimodal Fusion Mechanism and DPRPE) from calculating reliable disease risk estimates.

Furthermore, owners may mention absent symptoms (*"no vomiting"*) that risk being parsed as active clinical complaints, or they may report life-threatening red-flag emergencies (*"collapsed and struggling to breathe"*) that require immediate emergency triage redirection rather than routine diagnostic intake.

Owners need an empathetic, multi-turn conversational intake experience that actively spots missing clinical details, prompts for targeted clarification, isolates negated signs, intercepts acute emergencies, and assembles structured clinical evidence across canonical canine condition categories without attempting to autonomously diagnose diseases or prescribe medications.

---

## Solution

A **Conversational Clinical Intake Agent** backed by a **Multi-Task Transformer NLP Engine**. 

The intake agent guides dog owners through an interactive, multi-turn clinical consultation:
1. **Clinical Slot-Filling Dialogue**: Analyzes incoming owner descriptions using the NLP engine, detects missing essential variables (duration, anatomical location, laterality, progression trajectory, severity cues), and formulates targeted, veterinarian-approved clarifying questions whenever text quality falls below the clinical threshold.
2. **Explicit Negation Scoping**: Explicitly tracks negated symptoms as ruled-out historical observations, preventing them from improperly inflating active disease condition probabilities.
3. **Emergency Red-Flag Interceptor**: Continuously evaluates every user turn for life-threatening emergency cues (e.g. collapse, respiratory distress, cyanosis, seizures, severe poison ingestion), immediately halting non-urgent intake and issuing high-priority emergency veterinary clinic advisories.
4. **Calibrated Canonical Condition Probabilities**: Calibrates probabilities across four canonical canine health categories (`ear_inflammation`, `skin_condition`, `eye_condition`, `other`), calculating an independent text-quality score and model-confidence score to derive the composite modality reliability weight.
5. **Standardized Clinical Evidence Packet**: Upon consultation completion, packages the aggregated findings into an immutable structured payload (`SymptomParseResult`) formatted specifically for consumption by the Adaptive Multimodal Fusion Mechanism, DPRPE, and the clinic portal.

---

## User Stories

1. As a dog owner, I want to describe my dog's symptoms in plain conversational language across multiple turns, so that I can provide information naturally without knowing medical terminology.
2. As a dog owner who gives a brief or incomplete description (e.g. "he is scratching his ear"), I want the agent to ask follow-up questions about duration, laterality (left, right, or both), and severity, so that the clinical record is complete and accurate.
3. As a dog owner whose dog is in acute, life-threatening distress (e.g. collapse, cyanosis, gasping for air), I want an immediate emergency alert advising me to visit the nearest emergency veterinary hospital, so that critical care is not delayed by diagnostic intake.
4. As a dog owner mentioning resolved or absent symptoms (e.g. "he stopped vomiting", "no eye discharge"), I want the agent to record these as negated history rather than active symptoms, so that the assessment is not misdirected.
5. As a dog owner, I want clear explanations of the agent's working assumptions and primary differential impressions, so that I understand why specific follow-up questions are being asked.
6. As the Confidence-Weighted Adaptive Multimodal Fusion Mechanism, I want calibrated condition probabilities across the 4 canonical categories (`ear_inflammation`, `skin_condition`, `eye_condition`, `other`), so that text evidence can be combined with image analysis and wearable sensor metrics.
7. As the Confidence-Weighted Adaptive Multimodal Fusion Mechanism, I want a separate `text_quality_score` (0.0 to 1.0) and `model_confidence` (0.0 to 1.0) alongside a composite harmonic reliability score, so that I can properly weight the text modality stream against sensor and vision streams.
8. As the Disease Progression and Risk Prediction Engine (DPRPE), I want normalized duration entities (`{value, unit}`), progression trajectory (`worsening`, `improving`, `stable`), and new symptom alerts, so that I can model longitudinal canine disease trajectories.
9. As a veterinarian reviewing a consultation in the clinic portal, I want exact character spans highlighted on the owner's original text alongside conversation turn history, so that I can verify the agent's interpretation against the owner's exact words.
10. As a veterinarian, I want the intake agent to strictly refrain from prescribing medications or issuing definitive diagnoses, so that veterinary physical examination and clinical judgment remain authoritative.
11. As a clinic administrator, I want each consultation session to be associated with a registered Dog record, so that longitudinal medical history is preserved in the patient profile.
12. As an API client, I want structured session endpoints (`POST /api/v1/intake/sessions`, `POST /api/v1/intake/sessions/{id}/turns`, `POST /api/v1/intake/sessions/{id}/complete`), so that mobile apps and clinic portals can implement interactive chat interfaces easily.
13. As a backend developer, I want the intake agent to function with a deterministic zero-dependency stub engine during tests and CI, so that the entire test suite executes in seconds on CPU without multi-gigabyte neural weight downloads.
14. As an ML engineer, I want leak-free dog-level dataset splitting (`pet_id`) in offline training scripts (`ml/nlp/train.py`), so that repeated observations from the same dog do not contaminate evaluation benchmarks.
15. As a compliance auditor, I want every consultation record to track the model version identifier, so that predictions satisfy clinical traceability standards.

---

## Implementation Decisions

### 1. Architectural Boundaries & Placement
- **Feature Module Placement**: The intake consultation application use cases and presentation routes are placed directly within `app/features/symptom_nlp/` (utilizing `ConductIntakeTurnUseCase`, `StartIntakeSessionUseCase`, and `CompleteIntakeSessionUseCase`), ensuring tight cohesion with NLP entities, preprocessing heuristics, and inference engine adapters without introducing circular dependencies.
- **Inference Engine Protocol Compliance**: The agent interacts exclusively with `NLPSymptomEngineProtocol`. The existing dual-engine pattern is maintained: `StubNLPSymptomEngine` serves unit tests, development, and offline CI; `TrainedNLPSymptomEngine` serves production environments when fine-tuned weights exist in `model_registry/nlp/symptom_distilbert_v1/`.

### 2. Multi-Turn Session Modeling & State Accumulation
- **Session Entity**: An `IntakeSession` entity tracks `session_id`, `dog_id`, `created_at`, `updated_at`, `turn_count`, `messages` (role: user/agent, text, timestamp), `accumulated_evidence` (`SymptomParseResult`), `missing_slots` (e.g. duration, location laterality, progression), and `status` (`in_progress`, `completed`, `emergency_diverted`).
- **Context Synthesis Across Turns**: When an owner supplies supplementary information in turn $N$, the agent unions newly identified symptoms, resolves missing anatomical details (e.g. linking "left" to previously identified "ear"), updates duration, and recalculates condition probabilities on the synthesized consultation narrative.

### 3. Slot-Filling Heuristic & Clarifying Prompt Generator
- **Slot Evaluation Rubric**: Following each user turn, the agent evaluates four critical clinical slots:
  - **Symptom Slot**: At least one affirmative symptom keyword extracted.
  - **Anatomical Slot**: Body part and laterality (left/right/both) captured.
  - **Temporal Slot**: Onset duration with value and unit captured.
  - **Dynamic Slot**: Progression trajectory (`worsening`, `improving`, `stable`) or severity cue captured.
- **Prompt Generator**: If `text_quality_score` < 0.70 or critical slots remain unfulfilled after turn 1, the agent selects a targeted, veterinary-approved clarifying prompt focusing on the highest-priority missing slot. Maximum intake depth is capped at 4 turns to avoid user fatigue.

### 4. Emergency Red-Flag Interceptor
- **Deterministic Pre-Filter**: Prior to general slot extraction, every user message passes through `check_emergency_triage()`. If critical keywords (collapse, blue gums/cyanosis, respiratory distress, seizures, uncontrolled bleeding, poisoning) are detected:
  - The session status immediately shifts to `emergency_diverted`.
  - An emergency response banner is returned with prominent hospital referral instructions.
  - Standard condition probabilities are suppressed or zeroed to prevent false reassurance.

### 5. API Contracts

#### Start Intake Session (`POST /api/v1/symptoms/intake/sessions`):
```json
// Request
{
  "dog_id": "dog_123",
  "initial_text": "My dog has been scratching his ear."
}

// Response Envelope
{
  "success": true,
  "data": {
    "session_id": "intake_abc123",
    "dog_id": "dog_123",
    "turn_number": 1,
    "agent_message": "I understand your dog is scratching their ear. To help assess this properly: which ear is affected (left, right, or both), and how many days has this been happening?",
    "missing_slots": ["body_location_side", "duration"],
    "current_parse": {
      "symptoms": ["scratching"],
      "body_locations": [{"part": "ear", "side": null}],
      "duration": null,
      "text_quality_score": 0.50,
      "model_confidence": 0.82,
      "condition_probabilities": {
        "ear_inflammation": 0.75,
        "skin_condition": 0.15,
        "eye_condition": 0.02,
        "other": 0.08
      }
    },
    "emergency_triage": {"is_critical": false},
    "is_complete": false
  },
  "message": "Intake session started"
}
```

#### Submit Conversation Turn (`POST /api/v1/symptoms/intake/sessions/{session_id}/turns`):
```json
// Request
{
  "message": "It is the left ear, and it started 3 days ago. It seems to be getting worse."
}

// Response
{
  "success": true,
  "data": {
    "session_id": "intake_abc123",
    "turn_number": 2,
    "agent_message": "Thank you for clarifying. I've noted that the scratching in the left ear has been worsening over the past 3 days. Are you noticing any redness, discharge, or foul odor from the ear?",
    "missing_slots": [],
    "current_parse": {
      "symptoms": ["scratching"],
      "body_locations": [{"part": "ear", "side": "left"}],
      "duration": {"value": 3, "unit": "days"},
      "progression": "worsening",
      "text_quality_score": 0.88,
      "model_confidence": 0.86,
      "modality_reliability_score": 0.87,
      "condition_probabilities": {
        "ear_inflammation": 0.85,
        "skin_condition": 0.08,
        "eye_condition": 0.02,
        "other": 0.05
      }
    },
    "emergency_triage": {"is_critical": false},
    "is_complete": false
  },
  "message": "Turn processed successfully"
}
```

#### Finalize Intake Session (`POST /api/v1/symptoms/intake/sessions/{session_id}/complete`):
Returns the finalized, immutable `SymptomParseResult` ready for persistence and handoff to the Adaptive Multimodal Fusion Mechanism and DPRPE.

---

## Testing Decisions

### Seams Under Test

1. **Public Web API Seam (`POST /api/v1/symptoms/intake/*`)** *(Highest Seam)*:
   - Exercised via `httpx.AsyncClient` against the FastAPI application.
   - Tests complete multi-turn conversational lifecycles: starting a session, providing missing duration/location clarifications, verifying slot updates, detecting emergency diversions, and finalizing the session.
   - Asserts on status codes, Pydantic response envelope structure, and header conventions.

2. **Application Use Case Seam (`ConductIntakeTurnUseCase`)**:
   - Pure Python unit tests asserting on state progression, slot-filling logic, negation tracking, and text quality adjustments across simulated dialogue turns.
   - Injected with `StubNLPSymptomEngine` for instant execution without network or GPU dependencies.

3. **Clinical Emergency & Safety Seam**:
   - Tests emergency keyword interception during intake turns.
   - Asserts that acute signs (collapse, respiratory distress) instantly trigger `emergency_diverted` status and appropriate hospital referral messages.

4. **Multi-Task ML Pipeline & Leak-Free Dataset Seam (`ml/nlp/train.py`, `ml/nlp/evaluate.py`)**:
   - Tested using synthetic multi-dog seed data.
   - Asserts that `pet_id` groupings do not leak between train, validation, and test splits.
   - Verifies that evaluation calculates Macro-F1 across the 4 condition classes and reports Expected Calibration Error (ECE).

### Test Principles
- **Black-Box Observable Behavior**: Tests assert only on clinical extractions, slot states, status codes, and probabilities—never on internal Transformer weight matrices or private session caches.
- **Zero-GPU Dependency**: All standard test suites execute on CPU using heuristic stubs, completing in < 1 second.

---

## Out of Scope

- Autonomous medical prescription or therapy recommendation.
- Definitive disease diagnosis without veterinary physical examination.
- Multi-lingual tokenization (English only for this release).
- Audio speech-to-text recording (voice notes will be handled in a subsequent voice-intake feature).
- Image or sensor signal processing (handled by vision and behavioural modules).

---

## Further Notes

- The resulting `SymptomParseResult` payload matches the exact schema consumed by the Confidence-Weighted Adaptive Multimodal Fusion Mechanism.
- Model artifacts generated by offline training are saved to `model_registry/nlp/symptom_distilbert_v1/` and kept out of Git.
