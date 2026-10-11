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

**Owner**:
The user who registered a Dog and controls its data (account role `CLIENT`).
_Avoid_: Client, customer, pet parent

**Veterinarian**:
A user with the `VET` role and a professional profile; hidden from discovery until an administrator verifies them.
_Avoid_: Doctor, staff member, provider

**Patient**:
A Dog as seen by one Veterinarian: it has a live appointment with them, or its Owner has a conversation with them, and the Owner still shares data with veterinarians.
_Avoid_: Client dog, case

**Prediction**:
The stored outcome of one Assessment: a suspected condition, a combined progression risk and a confidence, kept as decision support and never as a diagnosis.
_Avoid_: Diagnosis, result, alert

**Progression Risk**:
The 0-100 estimate of a Dog's condition worsening over the next seven days, banded low (0-29), moderate (30-59), high (60-84) and critical (85-100).
_Avoid_: Severity, health score

**Baseline**:
A Dog's own average for a health metric over the 90 days before the period being shown; readings are judged abnormal against it, not against a breed norm.
_Avoid_: Normal range, reference value

**Reading**:
One measured value of a health metric for a Dog at a moment in time.
_Avoid_: Data point, sample, measurement

**Care Task**:
A dated preventive-care item for a Dog (vaccination, deworming, grooming and so on) that its Owner marks done.
_Avoid_: Reminder (a reminder is a Care Task shown on the dashboard), to-do
