---
name: ml-feature
description: Guide and runbook for scaffolding and implementing AI/ML feature modules in Canivue API. Use when adding vision, sensor/behavioural, NLP, multi-modal fusion, or risk progression AI modules adhering to Clean Architecture.
---

# AI/ML Feature Scaffolding & Implementation Guide

In **Canivue API**, AI/ML inference lives inside the backend as regular feature modules following Clean Architecture. ML frameworks (`torch`, `transformers`, `opencv`, etc.) are treated as external dependencies hidden behind domain protocols, exactly like database engines.

Offline model training, experimentation, and dataset preparation live separately in `ml/` at the repository root, producing versioned checkpoints stored in `model_registry/`.

---

## Architecture Flow for AI/ML Features

```
Presentation (FastAPI Router, Pydantic Schemas, Dependency Injection)
    ↓
Application (Use Cases, DTOs)
    ↓
Domain (Entities, Exceptions, <X>InferenceEngineProtocol, RepositoryProtocol)
    ↑
Infrastructure (SQLAlchemy Models, Repositories, infrastructure/ml/ Engine & Preprocessing)
```

### Layer Rules for AI/ML
1. **Domain (`domain/repositories.py`)**:
   - Declare `<X>InferenceEngineProtocol` as a Python `typing.Protocol`.
   - Methods take domain types or raw input bytes/arrays and return domain prediction entities/value objects.
   - **NEVER** import PyTorch, TensorFlow, OpenCV, or Transformers in the domain.
2. **Application (`application/use_cases.py`)**:
   - Coordinates business workflow (e.g., validate dog identity, call inference engine protocol, persist assessment record).
   - Depends **only** on the domain protocols via dependency injection.
   - Remains 100% unit-testable without any ML libraries installed.
3. **Infrastructure (`infrastructure/ml/`)**:
   - `preprocessing.py`: Cheap, lightweight input-quality and validation checks (dimensions, audio duration, sensor sample rate).
   - `engine.py`: Defines:
     - `Stub<X>Engine`: Deterministic, zero-dependency stub returning realistic predictions. Used in unit tests, dev mode, and CI.
     - `Trained<X>Engine`: Real engine loading weights from `model_registry/` using framework libraries. Only instantiated if enabled by settings.
4. **Presentation (`presentation/dependencies.py` & `router.py`)**:
   - FastAPI dependencies inject either `Stub<X>Engine` or `Trained<X>Engine` based on `app.config.Settings`.
   - Router receives multipart file uploads or JSON sensor arrays, validates request schemas, and delegates to the use case.

---

## Offline Training vs. Serving Split

| Responsibility | Location | Dependencies |
| :--- | :--- | :--- |
| **Online Inference & Serving** | `app/features/<feature>/` | `requirements.txt` (FastAPI, SQLAlchemy, Pydantic) |
| **Offline Training & Evaluation** | `ml/<modality>/` | `requirements-ml.txt` (torch, transformers, etc.) |
| **Model Artifacts** | `model_registry/<modality>/` | Gitignored checkpoint binaries + README metadata |

### Dog-Level Data Splitting
Always use `ml.common.data_splitting.dog_level_train_val_test_split` when training. Never split at the frame/sample level, which causes data leakage across the same dog!

### Common Metrics & Calibration
Always report metrics using `ml.common.metrics` (Accuracy, Macro-F1, ROC-AUC, Brier Score, and Expected Calibration Error `ECE`).

---

## Step-by-Step Implementation Checklist

1. **Domain**:
   - [ ] Define domain entity in `app/features/<feature>/domain/entities.py`.
   - [ ] Define exceptions in `app/features/<feature>/domain/exceptions.py`.
   - [ ] Declare `<X>InferenceEngineProtocol` in `app/features/<feature>/domain/repositories.py`.
2. **Application**:
   - [ ] Create input/output DTOs in `app/features/<feature>/application/dtos.py`.
   - [ ] Implement use cases in `app/features/<feature>/application/use_cases.py`.
3. **Infrastructure**:
   - [ ] Implement `preprocessing.py` for input validation.
   - [ ] Implement `Stub<X>Engine` and `Trained<X>Engine` in `infrastructure/ml/engine.py`.
   - [ ] Implement persistence models and repositories in `infrastructure/models.py` and `infrastructure/repositories.py`.
4. **Presentation**:
   - [ ] Create Pydantic schemas in `presentation/schemas.py`.
   - [ ] Provide dependency injection in `presentation/dependencies.py`.
   - [ ] Create endpoints in `presentation/router.py`.
   - [ ] Register router in `app/main.py`.
5. **Testing**:
   - [ ] Unit tests for use cases with `Stub<X>Engine` in `tests/features/<feature>/test_use_cases.py`.
   - [ ] HTTP endpoint integration tests with `httpx.AsyncClient` in `tests/features/<feature>/test_api.py`.
