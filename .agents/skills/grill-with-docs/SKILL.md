---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which simultaneously creates and updates documentation (ADRs in docs/adr/ and domain terms in GLOSSARY.md) as decisions crystallize.
---

# Grill With Docs

This skill combines **relentless interrogation** (from `grilling`, `.agents/skills/grilling/SKILL.md`) with **active domain documentation** (from `domain-modeling`, `.agents/skills/domain-modeling/SKILL.md`).

---

## 1. The Grilling Loop

Interview the user in **rounds** to map a **design tree** until every branch is resolved:

- The **frontier** is every decision whose prerequisites are settled.
- Present all questions on the frontier in one round:
  ```markdown
  ❓ **Q1** - **<question title>**: <question body with choices>
  ➡️ <your recommended answer>
  ---
  ❓ **Q2** - **<question title>**: <question body with choices>
  ➡️ <your recommended answer>
  ```
- **Find facts yourself**: Inspect files, configurations, and schemas directly before asking.
- When user answers arrive, recompute the frontier and proceed to the next round.

---

## 2. Active Domain Modeling & Documentation

As decisions crystallize during the interview:

### Update `GLOSSARY.md`
- Challenge fuzzy language: "You say 'sample', do you mean a dog profile, a sensor capture, or a test run?"
- Update or create `GLOSSARY.md` at the project root the moment a term is defined or clarified.
- Follow the format:
  ```markdown
  **Canonical Term**:
  A concise 1-2 sentence definition of what it IS.
  _Avoid_: Confusing synonyms or deprecated terms
  ```

### Record Architectural Decisions (`docs/adr/`)
- When a decision is:
  1. **Hard to reverse**
  2. **Surprising without context**
  3. **The result of a real trade-off**
- Create an ADR in `docs/adr/NNNN-<slug>.md` (e.g. `docs/adr/0001-modular-monolith-clean-arch.md`).
- Keep it tight (1-3 sentences: context, decision, rationale).

---

## Completion Criteria

The session is done when:
1. The question frontier is empty (no assumptions remain).
2. The user confirms shared understanding.
3. Any new or clarified domain terms are committed to `GLOSSARY.md`.
4. Any non-obvious architecture choices are recorded in `docs/adr/`.
