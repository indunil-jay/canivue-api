---
name: clean-architecture-feature
description: Guide for scaffolding and implementing clean architecture features in Canivue API. Use when creating new standard (non-ML) business features such as dogs, users, clinics, or assessments.
---

# Clean Architecture Feature Scaffolding Guide

In **Canivue API**, all business logic is organized into self-contained feature modules under `app/features/<feature_name>/` adhering strictly to Clean Architecture and the Dependency Inversion Principle.

---

## Directory Structure

```
app/features/<feature_name>/
├── __init__.py
├── domain/                      # 1. Pure business logic & interfaces
│   ├── __init__.py
│   ├── entities.py              # Domain entities (subclass BaseEntity)
│   ├── exceptions.py            # Domain-specific exceptions
│   └── repositories.py          # Repository Protocol interfaces
├── application/                 # 2. Orchestration & Use Cases
│   ├── __init__.py
│   ├── dtos.py                  # Input and Output DTO dataclasses
│   └── use_cases.py             # Single-responsibility use cases
├── infrastructure/              # 3. DB & External Adapters
│   ├── __init__.py
│   ├── models.py                # SQLAlchemy ORM models
│   └── repositories.py          # SQLAlchemy repository implementations
└── presentation/                # 4. Web API & Delivery
    ├── __init__.py
    ├── schemas.py               # Pydantic request/response schemas
    ├── dependencies.py          # FastAPI Depends() providers
    └── router.py                # APIRouter route definitions
```

---

## The Inward Dependency Rule

Dependencies strictly point **inwards**:
- `Presentation` depends on `Application` and `Domain`.
- `Infrastructure` implements protocols defined in `Domain`.
- `Application` depends **only** on `Domain`.
- `Domain` has **zero external framework dependencies** (no FastAPI, no SQLAlchemy, no Pydantic).

---

## Step-by-Step Implementation Flow

### 1. Domain Layer
- Inherit from `app.shared.entity.BaseEntity` in `entities.py`.
- Define custom domain exceptions inheriting from `app.core.exceptions.AppException` in `exceptions.py`.
- Define repository protocol in `repositories.py` inheriting from `typing.Protocol` (or `app.shared.repository.BaseRepositoryProtocol`).

### 2. Application Layer
- Define clear input and output dataclasses in `dtos.py`.
- Create Use Cases in `use_cases.py` receiving repository protocols in `__init__` and implementing `async def execute(self, dto: ...)` methods.

### 3. Infrastructure Layer
- Define SQLAlchemy models inheriting from `app.core.database.Base` in `models.py`.
- Implement concrete repositories in `repositories.py` taking `AsyncSession` and converting ORM models to domain entities.

### 4. Presentation Layer
- Define Pydantic v2 schemas in `schemas.py`.
- Provide FastAPI dependency injection providers in `dependencies.py` returning instantiated use cases with database sessions.
- Expose REST endpoints in `router.py` returning standard `app.core.response.APIResponse` structures.
- Register the router in `app/main.py`:
  ```python
  from app.features.<feature_name>.presentation.router import router as <feature_name>_router
  app.include_router(<feature_name>_router, prefix="/api/v1/<feature_name>s", tags=["<FeatureName>"])
  ```

### 5. Automated Tests
- Unit tests: Test use cases with mock or in-memory repository implementations in `tests/features/<feature_name>/test_use_cases.py`.
- Integration tests: Test FastAPI endpoints with `httpx.AsyncClient` and SQLite in-memory test database in `tests/features/<feature_name>/test_api.py`.
