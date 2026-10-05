# Canivue Domain Glossary

Canonical vocabulary and definitions for the Canivue API project.

## Language

**Dog**:
The canine patient or subject registered in the system undergoing diagnostic assessment.
_Avoid_: Pet, animal, patient (use Dog)

**Assessment**:
A complete evaluation session for a dog, combining one or more diagnostic modalities (vision, behaviour/sensors, symptom extraction, fusion).
_Avoid_: Exam, checkup, test session

**Feature Module**:
A decoupled, self-contained business slice under `app/features/<feature>/` structured in four clean-architecture layers: domain, application, infrastructure, presentation.
_Avoid_: Service, microservice, package

**Inference Engine**:
An adapter implementing `<X>InferenceEngineProtocol` that produces machine learning predictions from inputs.
_Avoid_: ML service, model runner, predictor

**Stub Engine**:
A zero-dependency, deterministic test adapter (`Stub<X>Engine`) fulfilling the inference protocol without requiring ML framework installations (PyTorch, TensorFlow, etc.).
_Avoid_: Mock model, fake predictor

**Model Registry**:
The versioned storage directory (`model_registry/<modality>/`) for trained binary model checkpoints and README metadata, kept outside of version control.
_Avoid_: Model store, weights repo

**Seam**:
The public boundary where testing and module interaction occurs (e.g. use case execution method with DTOs, or REST API endpoint with AsyncClient).
_Avoid_: Internal boundary, private interface

**Symptom Parsing**:
The extraction of structured clinical concepts (symptom, body location, duration, frequency, progression, severity cues) and condition probabilities from informal owner text.
_Avoid_: Medical text summarization, symptom chatbot

**Text Quality Score**:
A deterministic heuristic score (0.0 to 1.0) assessing the clinical completeness and syntactic informativeness of owner-written text for adaptive fusion.
_Avoid_: Text confidence, text length score

**Model Confidence**:
The NLP model's estimated prediction certainty (0.0 to 1.0) regarding its symptom extraction and condition classification.
_Avoid_: Text quality score (keep confidence and quality strictly separate)

**Negated Symptom**:
A clinical sign explicitly described by the dog owner as absent, stopped, or resolved (e.g., "no vomiting", "stopped scratching"), preserved for differential diagnostic history but excluded from active condition probability inflation.
_Avoid_: Inactive symptom, ignored symptom

**Emergency Triage Flag**:
An automated clinical safety alert triggered when owner text contains life-threatening cues (collapse, respiratory distress, cyanosis, seizures, severe trauma) advising immediate emergency veterinary care.
_Avoid_: Urgent symptom, severe warning

**Modality Reliability Score**:
The composite reliability weight (0.0 to 1.0) calculated from text quality and prediction confidence, consumed by the Adaptive Multimodal Fusion Mechanism to balance the NLP evidence stream.
_Avoid_: Text weight, NLP confidence


