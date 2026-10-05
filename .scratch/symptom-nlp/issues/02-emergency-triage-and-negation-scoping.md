# 02: Emergency Red-Flag Triage Interceptor and Negation Scoping

**What to build:** Clinical safety guardrails and negation understanding in the symptom parser. If an owner enters text containing critical acute symptoms (e.g. *"my dog collapsed and is struggling to breathe"*), the API immediately surfaces an `emergency_triage` alert flag (`is_critical: true`) with actionable advice to seek urgent emergency care. When symptoms are mentioned as absent or resolved (e.g. *"no vomiting"*, *"stopped scratching"*), they are scoped as `negated: true`, segregated into `negated_symptoms`, and excluded from active condition probability calculations so differential diagnoses are not skewed.

**Blocked by:** 01: Core Clean Architecture Scaffolding and Stub API Endpoint

**Status:** ready-for-agent

## Acceptance Criteria

- [ ] `preprocessing.py` implements an emergency keyword triage detector covering acute respiratory, cardiovascular, toxicological, and neurological red flags.
- [ ] Emergency alert schema (`EmergencyTriageAlert`) returned in API payload whenever acute cues are detected, with empty/safe defaults otherwise.
- [ ] Negation scope detector recognizes common negation particles ("no", "not", "stopped", "never", "without", "resolved") within symptom windows.
- [ ] Negated symptoms are retained in `negated_symptoms` for clinical history but excluded from `symptoms` and condition probability calculations.
- [ ] Unit tests verify emergency trigger phrases and safe non-emergency phrases.
- [ ] Unit tests verify negation scoping on sentences containing mixed active and negated symptoms.
