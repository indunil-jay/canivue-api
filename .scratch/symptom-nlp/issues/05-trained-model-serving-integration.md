# 05: Real Model Serving Integration (TrainedNLPSymptomEngine)

**What to build:** The integration bridge connecting the trained model artifacts in `model_registry/nlp/` with the Clean Architecture web serving layer. Implements `SymptomParserPipeline` in `ml/nlp/pipeline.py` that loads model weights and tokenizers, runs multi-task inference, decodes entity spans, executes temporal/negation rules, and formats structured outputs. Implements `TrainedNLPSymptomEngine` in `app/features/symptom_nlp/infrastructure/ml/engine.py` fulfilling `NLPSymptomEngineProtocol`. Configures dependency injection to dynamically serve the trained model when real models are enabled in configuration (`USE_REAL_ML_MODELS = True`), maintaining 100% contract compatibility with the stub engine.

**Blocked by:** 02: Emergency Red-Flag Triage Interceptor and Negation Scoping, 03: Temporal Duration Normalization, Frequency Mapping, and Span Offsets, 04: Offline Multi-Task Training Pipeline (ml/nlp)

**Status:** ready-for-agent

## Acceptance Criteria

- [ ] `ml/nlp/pipeline.py` implements `SymptomParserPipeline` supporting single and batch inference with automatic fallback for cold starts.
- [ ] `TrainedNLPSymptomEngine` loads model weights from `MODEL_REGISTRY_DIR/nlp/<checkpoint>` and conforms strictly to `NLPSymptomEngineProtocol`.
- [ ] FastAPI dependency injection provider conditionally supplies `TrainedNLPSymptomEngine` or `StubNLPSymptomEngine` based on application settings.
- [ ] Response stamps `model_version` matching the checkpoint identifier for audit compliance (FR-16).
- [ ] Integration tests verify that swapping from stub to trained engine produces valid API responses matching the exact same schema.
