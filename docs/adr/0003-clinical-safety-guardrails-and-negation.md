# 0003. Clinical Safety Guardrails, Negation Scoping, and Modality Reliability

We have decided to incorporate explicit emergency triage interceptors, negation scoping, and composite reliability scoring into the NLP symptom parser module.

## Context
Dog owners describe symptoms with varying levels of urgency and phrasing, often mentioning absent or resolved symptoms ("not scratching anymore", "no vomiting"), and occasionally reporting acute life-threatening conditions ("dog collapsed and has blue gums"). If the system treats all mentioned entities uniformly, it risks producing false-positive diagnoses or failing to warn users of life-threatening emergencies. Additionally, downstream multimodal fusion requires an unambiguous measure of NLP reliability.

## Decision
1. **Stateless Transformation with Assessment Hook**: Provide a stateless parsing endpoint (`POST /api/v1/symptoms/parse`) for interactive drafts, which can be linked to dog assessment entities by the application layer.
2. **Explicit Negation Scoping**: Extracted symptoms include a `negated: bool` property. When true, the symptom is placed in `negated_symptoms`, retained in history, but excluded from active condition probability calculations.
3. **Emergency Red-Flag Interceptor**: Implement a deterministic keyword guardrail in `infrastructure/ml/preprocessing.py` that intercepts critical clinical emergencies (collapse, respiratory distress, cyanosis, seizures, severe poison ingestion) and returns an immediate `emergency_triage` alert advising urgent veterinary intervention.
4. **Modality Reliability Score**: Compute an aggregated reliability score $\text{Reliability} = \frac{2 \times Q \times C}{Q + C}$ (harmonic mean of text quality $Q$ and model confidence $C$) alongside individual metrics for seamless consumption by the Adaptive Multimodal Fusion Mechanism.
5. **Fail-Safe Language Validation**: If input text contains no recognizable anatomical or clinical concepts or is non-English, return low quality/confidence with explicit warning codes (`INSUFFICIENT_SYMPTOM_INFORMATION`, `UNSUPPORTED_LANGUAGE`) rather than hallucinating predictions.

## Consequences
- Prevents clinical misdiagnosis caused by negated symptoms.
- Protects dog health through immediate emergency safety alerts.
- Provides a clean, standardized contract for Adaptive Multimodal Fusion.
