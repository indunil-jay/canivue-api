---
name: implement
description: Implement a piece of work based on a spec, set of tickets, or user prompt using Test-Driven Development (TDD) and clean architecture standards.
---

# Implement

Implement the work described by the user in the specification or tickets, adhering strictly to the red-green-refactor cycle and project architecture.

---

## 1. Context & Seams
1. **Locate the Spec/Tickets**: Read the originating issue, spec, or tickets (on GitHub via `gh issue view` or local tickets).
2. **Consult Domain Docs**: Read `GLOSSARY.md` and relevant ADRs in `docs/adr/`.
3. **Agree on Public Seams**:
   - Determine the public interfaces to test against (e.g. Use Case `execute()` method with DTOs, or FastAPI route with `AsyncClient`).
   - Do **not** test private methods or internal framework plumbing.
   - For AI/ML features, test against the `<X>InferenceEngineProtocol` with `Stub<X>Engine`.

---

## 2. The TDD Implementation Loop
Follow the `tdd` skill (`.agents/skills/tdd/SKILL.md`):
1. **Red**: Write a failing unit or integration test at the agreed seam. Run it to confirm it fails for the expected reason:
   ```bash
   pytest tests/features/<feature>/test_use_cases.py -k <test_name>
   ```
2. **Green**: Write the minimal production code necessary to pass the test.
3. **Verify**:
   - Run the single test file:
     ```bash
     pytest tests/features/<feature>/test_use_cases.py
     ```
   - Check linting / formatting:
     ```bash
     ruff check app/
     ```
4. Repeat for each slice until the ticket or spec criteria are met.

---

## 3. Full Verification
Once all slices are implemented:
1. Run the entire test suite:
   ```bash
   pytest
   ```
2. Ensure no linting regressions exist:
   ```bash
   ruff check .
   ```

---

## 4. Code Review & Commit
1. Review the diff against standards and spec using `code-review` (`.agents/skills/code-review/SKILL.md`).
2. Fix any code smells or spec gaps identified.
3. Commit changes following `standard-git-commit` (`.agents/skills/standard-git-commit/SKILL.md`).
