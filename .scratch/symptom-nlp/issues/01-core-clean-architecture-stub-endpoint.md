# 01: Core Clean Architecture Scaffolding and Stub API Endpoint

**What to build:** An end-to-end REST API endpoint (`POST /api/v1/symptoms/parse`) built with Clean Architecture in `app/features/symptom_nlp/`. An API client or frontend can submit a JSON payload containing freeform dog symptom text and receive a validated, structured JSON response containing normalized symptoms, preliminary condition probabilities, text quality score, and model confidence. The feature is powered by a zero-dependency, deterministic `StubNLPSymptomEngine` so that the entire flow runs instantly without requiring PyTorch or GPU hardware.

**Blocked by:** None (can start immediately)

**Status:** resolved

## Acceptance Criteria

- [x] Domain layer (`domain/entities.py`, `domain/repositories.py`) defines pure entities (`SymptomParseResult`, `ConditionProbability`, `EmergencyTriageAlert`) and the `NLPSymptomEngineProtocol` with zero framework dependencies.
- [x] Application layer (`application/use_cases.py`, `application/dtos.py`) coordinates input parsing and invokes the engine protocol.
- [x] Infrastructure layer (`infrastructure/ml/engine.py`, `infrastructure/ml/preprocessing.py`) implements `StubNLPSymptomEngine` with baseline heuristic symptom extraction, 4-class condition probabilities (`ear_inflammation`, `skin_condition`, `eye_condition`, `other`), and initial text quality scoring.
- [x] Presentation layer (`presentation/schemas.py`, `presentation/dependencies.py`, `presentation/router.py`) exposes `POST /api/v1/symptoms/parse` returning standard `APIResponse` envelopes.
- [x] Router registered in `app/main.py` under prefix `/api/v1/symptoms`.
- [x] Unit tests in `tests/features/symptom_nlp/test_use_cases.py` verify use case behavior.
- [x] Integration tests in `tests/features/symptom_nlp/test_api.py` verify HTTP status codes, validation errors, and response shapes with `httpx.AsyncClient`.
