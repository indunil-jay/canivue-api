# 0002. NLP Symptom Parser Multi-Task Architecture and Offline Pipeline

We have decided to implement the NLP Symptom Parser as a multi-task Transformer architecture in `ml/nlp/` with deterministic normalizers, wrapped by a Clean Architecture feature in `app/features/symptom_nlp/`.

## Context
Canivue requires converting informal dog owner descriptions into structured symptom evidence and condition probabilities for the downstream Adaptive Fusion Mechanism and the Disease Progression and Risk Prediction Engine (DPRPE). The module must extract diverse semantic concepts (symptoms, locations, durations, frequency, severity, progression, behaviour) while predicting probabilities for 4 condition categories (`ear_inflammation`, `skin_condition`, `eye_condition`, `other`), and estimating text quality and model confidence independently.

## Decision
1. **Core Location (`ml/nlp/`)**: All model definitions, multi-task heads, feature normalizers, seed dataset generators, and training/evaluation loops live in `ml/nlp/`.
2. **Multi-Task Architecture**: A unified Transformer backbone (`distilbert-base-uncased` by default, swappable to `BiomedNLP-PubMedBERT`) with:
   - Token classification head for BIO span extraction (symptom, body location).
   - Sequence classification head for 4-class condition probabilities.
   - Deterministic post-processing for temporal duration normalization (`{value, unit}`) and frequency mapping.
3. **Loss Balancing**: Multi-task joint training weighted at $\alpha = 0.6$ (token-level NER loss) and $\beta = 0.4$ (sequence-level cross-entropy).
4. **Deterministic Text Quality Rubric**: Evaluated via a transparent weighted scoring rubric (symptom presence 30%, location 20%, duration 20%, severity/progression 15%, length/syntax 15%) kept separate from model prediction confidence.
5. **Clean Architecture Serving Adapter (`app/features/symptom_nlp/`)**:
   - Implements `NLPSymptomEngineProtocol` in the domain.
   - Provides `StubNLPSymptomEngine` with rule-based heuristics for fast, zero-dependency unit tests and CI.
   - Provides `TrainedNLPSymptomEngine` that delegates to `ml/nlp/pipeline.py` when real weights are available.
   - Exposes `POST /api/v1/symptoms/parse` returning normalized attributes plus character-level `spans` for veterinary UI highlighting.

## Consequences
- Fast inference suitable for CPU environments without heavy GPU hosting requirements.
- Full compatibility with the Adaptive Fusion Mechanism's input expectations.
- Continuous integration and automated tests remain fast and lightweight without downloading deep learning weights.
