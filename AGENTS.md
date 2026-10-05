# Canivue API — Agent Guidelines

Welcome to the **Canivue API** project. This file guides AI agents working across this repository.

---

## 🏛️ Architecture & Principles

Canivue API is built with **FastAPI**, **Async SQLAlchemy**, and **Feature-Based Clean Architecture** inside a **Modular Monolith**:
- Every feature lives in `app/features/<feature>/` with 4 strict layers:
  - `presentation/`: FastAPI routers, Pydantic schemas, dependency providers.
  - `application/`: Single-responsibility Use Cases and DTOs.
  - `domain/`: Pure business entities, exceptions, and `Protocol` interfaces (zero framework imports).
  - `infrastructure/`: SQLAlchemy models, concrete repositories, and `ml/` inference engines.
- **Inward Dependency Rule**: Presentation -> Application -> Domain <- Infrastructure.
- **AI/ML Engine Protocol**: Heavy ML libraries (`torch`, `transformers`) are NEVER imported into application or domain layers. Use Cases interact strictly with `<X>InferenceEngineProtocol`. Real engines live in `infrastructure/ml/engine.py`; stub engines (`Stub<X>Engine`) are provided for testing and default runs. Offline training lives in `ml/` outside the web application.

---

## 🧰 Agent Skills

Skills are located in `.agents/skills/<name>/SKILL.md` (and `.agent/skills/<name>/SKILL.md`).

### Core Workflow Skills
- **`wayfinder`**: Map large efforts into decision tickets on the issue tracker.
- **`grillme`** / **`grill-me`**: Relentless multi-round interview to stress-test plans and architectures before coding.
- **`grill-with-docs`**: Grilling interview that updates `GLOSSARY.md` and creates ADRs in `docs/adr/` as decisions crystallize.
- **`to-spec`**: Synthesize the conversation into a comprehensive spec published to the issue tracker.
- **`to-tickets`** (alias **`to-ticket`**): Break a spec into tracer-bullet vertical slice tickets with blocking dependencies.
- **`implement`**: Build features test-first (TDD), check types/lints, run code review, and commit.
- **`tdd`**: Test-driven development red-green-refactor loop at pre-agreed public seams.
- **`code-review`**: Two-axis review (Standards + Fowler smell baseline, and Spec conformance) with parallel sub-agents.
- **`retro`**: Retrospective analysis to improve agent navigation, automated checks, and standards.

### Project-Specific Skills
- **`ml-feature`**: Guide for implementing AI/ML feature modules with clean architecture, protocols, stub engines, and model registry.
- **`clean-architecture-feature`**: Step-by-step scaffolding for standard domain features (dogs, users, clinics).
- **`standard-git-commit`**: Conventional Commits specification for commit messages.

### Quality, Architecture & Delivery Skills
- **`diagnosing-bugs`**: Tight feedback loop discipline for isolating hard bugs and performance regressions.
- **`domain-modeling`**: Domain modeling rules for maintaining `GLOSSARY.md` and `docs/adr/`.
- **`codebase-design`**: Deep modules, seams, leverage, and locality vocabulary.
- **`improve-codebase-architecture`**: Scan for shallow modules and generate visual HTML architecture reports.
- **`implement-spec`**: High-concurrency spec implementer using task graphs and subagents.
- **`pr`**: Generate structured PR descriptions with evidence and blast radius.
- **`triage`**: Move issues and PRs through canonical triage states (`needs-triage`, `ready-for-agent`, etc.).
- **`prototype`**: Rapid throwaway prototypes to validate logic or UI.

---

## ⚙️ Configuration & Pointers

### Issue tracker
GitHub Issues via `gh` CLI. See [docs/agents/issue-tracker.md](file:///docs/agents/issue-tracker.md).

### Triage labels
Standard 5-state vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See [docs/agents/triage-labels.md](file:///docs/agents/triage-labels.md).

### Domain docs
Single-context repository layout (`GLOSSARY.md` at root, `docs/adr/` for ADRs). See [docs/agents/domain.md](file:///docs/agents/domain.md).

---

## 🧪 Development Commands

- **Run Dev Server**: `uvicorn app.main:app --reload --port 8000`
- **Run All Tests**: `pytest`
- **Run Feature Tests**: `pytest tests/features/<feature>/`
- **Lint Code**: `ruff check app/`
- **Format Code**: `ruff format app/`
