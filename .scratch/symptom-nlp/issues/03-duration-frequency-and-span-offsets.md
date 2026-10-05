# 03: Temporal Duration Normalization, Frequency Mapping, and Span Offsets

**What to build:** Precise temporal normalization and character-level span tracking in the symptom parser. Temporal phrases written in natural language (e.g. *"for three days"*, *"since yesterday"*, *"for 2 weeks"*) are normalized into `{value: int, unit: str}` objects for consumption by the DPRPE longitudinal engine. Frequency descriptors and progression trajectories (*worsening*, *improving*, *stable*) are mapped to standardized enum values. Every extracted entity records its raw text, category, and exact 0-indexed character `[start, end]` offsets so the veterinarian portal UI can highlight the supporting evidence directly on the owner's original text.

**Blocked by:** 01: Core Clean Architecture Scaffolding and Stub API Endpoint

**Status:** resolved

## Acceptance Criteria

- [x] Deterministic temporal duration parser converts numeric and word numerals (e.g. "three", "2") with units (hours, days, weeks, months) into `{value: int, unit: str}`.
- [x] Relative time phrases (e.g. "since yesterday" -> 1 day, "since this morning" -> hours) normalize accurately. Missing duration returns `null` without fabricating data.
- [x] Frequency and progression classifiers identify trajectory terms (`worsening`, `improving`, `stable`) and behavioural descriptors.
- [x] Extracted entities populate a `spans` array with `{entity: str, text: str, start: int, end: int, negated: bool}` verified against original string indices.
- [x] Full unit test suite asserting accuracy of duration normalization, frequency extraction, and span offset bounds.
