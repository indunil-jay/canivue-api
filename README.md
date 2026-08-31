# Canivue API

A decoupled, scalable backend built with **FastAPI**, **Modular Monolith Architecture**, and **Feature-Based Clean Architecture**.

---

## 🏛️ Architecture Overview

The codebase is organized as a **Modular Monolith**:
- **Core / Shared Kernel**: Common cross-cutting concerns (database connection, config, base protocols, response schemas, error handling).
- **Features (`app/features/`)**: Fully encapsulated, strongly decoupled business feature modules. Each feature follows Clean Architecture independently.

### 📐 Layer Dependency Rule

Within each feature module, dependencies flow strictly **inwards**:

```
Presentation (Routers, HTTP Schemas, Dependencies)
    ↓
Application (Use Cases, Commands, Queries, DTOs)
    ↓
Domain (Pure Business Entities, Protocols, Domain Exceptions)
    ↑
Infrastructure (SQLAlchemy Models, Concrete Repositories, External APIs)
```

1. **Domain Layer (`domain/`)**: Pure business logic without framework or ORM dependencies. Defines entities, business rules, and repository protocols (`Protocol`).
2. **Application Layer (`application/`)**: Coordinates business workflows via Use Cases. Accepts and returns DTOs.
3. **Infrastructure Layer (`infrastructure/`)**: Implements database models, queries, and external services fulfilling domain protocols.
4. **Presentation Layer (`presentation/`)**: Exposes HTTP endpoints (FastAPI routers), parses request schemas, handles response formatting, and sets up Dependency Injection.

---

## 📁 Project Folder Structure

```
canivue-api/
├── .gitignore                           # Excludes .agents/, virtualenvs, caches, etc.
├── requirements.txt                     # Production and development dependencies
├── pyproject.toml                       # Build & tool configurations (pytest, ruff)
├── .env.example                         # Environment variable template
├── README.md                            # Architecture & onboarding guide
│
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app entrypoint & router aggregation
│   ├── config.py                        # Pydantic Settings configuration
│   │
│   ├── core/                            # Cross-cutting foundational modules
│   │   ├── __init__.py
│   │   ├── database.py                  # Async SQLAlchemy engine & session dependency
│   │   ├── exceptions.py                # AppException hierarchy & global handlers
│   │   └── response.py                  # Standard APIResponse JSON envelope
│   │
│   ├── shared/                          # Shared kernel & base abstractions
│   │   ├── __init__.py
│   │   ├── entity.py                    # BaseEntity with ID & timestamps
│   │   └── repository.py                # Generic BaseRepositoryProtocol
│   │
│   └── features/                        # Self-contained feature modules
│       └── sample/                      # Sample Feature Blueprint
│           ├── __init__.py
│           ├── domain/                  # 1. Pure Domain Logic & Interfaces
│           │   ├── __init__.py
│           │   ├── entities.py          # SampleItem entity
│           │   ├── exceptions.py        # Domain exceptions
│           │   └── repositories.py      # SampleRepositoryProtocol
│           ├── application/             # 2. Use Cases & DTOs
│           │   ├── __init__.py
│           │   ├── dtos.py              # Input/Output DTOs
│           │   └── use_cases.py         # Create/Get/List/Update/Delete Use Cases
│           ├── infrastructure/          # 3. Persistence & Adapters
│           │   ├── __init__.py
│           │   ├── models.py            # SampleModel (SQLAlchemy)
│           │   └── repositories.py      # SQLAlchemySampleRepository
│           └── presentation/            # 4. Delivery / Web API
│               ├── __init__.py
│               ├── schemas.py           # Request & Response Pydantic models
│               ├── dependencies.py      # Dependency Injection providers
│               └── router.py            # APIRouter endpoints
│
└── tests/
    ├── __init__.py
    ├── conftest.py                      # In-memory test DB & AsyncClient fixtures
    └── features/
        └── sample/
            ├── __init__.py
            ├── test_use_cases.py        # Application Use Case tests
            └── test_api.py              # HTTP Integration tests
```

---

## 🚀 Getting Started

### 1. Prerequisites & Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
cp .env.example .env
```

### 3. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

- **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative API Docs (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Running Tests

```bash
pytest
```

---

## ➕ Adding a New Feature

To add a new feature (e.g. `dogs` or `users`):

1. **Create the folder structure inside `app/features/<feature_name>/`**:
   - `domain/` (`entities.py`, `exceptions.py`, `repositories.py`)
   - `application/` (`dtos.py`, `use_cases.py`)
   - `infrastructure/` (`models.py`, `repositories.py`)
   - `presentation/` (`schemas.py`, `dependencies.py`, `router.py`)
2. **Implement layers from inner (domain) to outer (presentation)**.
3. **Register the router** in [app/main.py](file:///c:/Users/shyam/Desktop/canivue-api/app/main.py):
   ```python
   from app.features.<feature_name>.presentation.router import router as <feature_name>_router

   app.include_router(<feature_name>_router, prefix="/api/v1/<feature_name>s", tags=["<FeatureName>"])
   ```
4. **Add tests** in `tests/features/<feature_name>/`.

---

## 🤖 Local Agent Skills (Untracked)

The local `.agents/skills/` directory provides workflow guides that assist development agents without polluting git history:
- `clean-architecture-feature`: Instructions and boilerplate rules for scaffolding new features.
- `standard-git-commit`: Guidelines for Conventional Commits.
