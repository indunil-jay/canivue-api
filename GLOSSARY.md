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
