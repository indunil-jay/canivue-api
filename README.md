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

## 🤖 AI/ML Architecture

AI/ML inference lives **inside** this backend as ordinary feature modules —
it does not need (or get) a separate repo. A vision/sensor/NLP model is just
another external dependency behind a `Protocol`, the same way SQLAlchemy is:

- **`app/features/<feature>/domain/repositories.py`** declares an
  `<X>InferenceEngineProtocol` alongside the usual persistence-repository
  Protocol. The application layer's use cases depend on that Protocol only —
  never on `torch`/`tensorflow`/`transformers`/`opencv` directly — so they
  stay unit-testable with zero ML frameworks installed.
- **`app/features/<feature>/infrastructure/ml/`** is the *only* place allowed
  to import those frameworks: `engine.py` holds a dependency-free
  `StubXEngine` (default, used in dev/tests/CI) and the real trained-model
  engine; `preprocessing.py` holds cheap input-quality checks.
- **Serving vs. training are split.** `app/` only *loads* a finished
  checkpoint and runs inference at request time. Offline training,
  experimentation, and evaluation live in **`ml/`** at the repo root, and
  read/write versioned checkpoints in **`model_registry/`** (gitignored —
  large binaries don't belong in git; see `model_registry/README.md`). This
  keeps `pip install -r requirements.txt && pytest` fast and GPU-free; heavy
  training deps are opt-in via `requirements-ml.txt`.

No AI feature is built yet — `app/features/sample/` remains the only
concrete feature module in the repo. What's scaffolded and ready is the
*supporting* structure this pattern needs: the offline training workspace
(`ml/`), the trained-checkpoint store (`model_registry/`), and the
opt-in heavy dependencies (`requirements-ml.txt`). The same shape applies to
each of the proposal's AI modules once built — vision, behavioural/sensor
analysis, NLP symptom extraction, the Confidence-Weighted Adaptive Fusion
Mechanism, and the Disease Progression and Risk Prediction Engine (DPRPE).
Full guide: [`.agents/skills/ml-feature/SKILL.md`](.agents/skills/ml-feature/SKILL.md).

```
canivue-api/
├── app/features/<feature_name>/       # Each AI feature, once added: same 4 layers, + infrastructure/ml/
├── ml/                                 # Offline training & evaluation (not imported by app/)
│   ├── common/                         # Shared metrics, dog-level data splitting
│   ├── vision/                         # EfficientNet training (worked example)
│   ├── behavioural/                    # 1D-CNN-LSTM training (skeleton)
│   └── nlp/                            # Symptom-model training (skeleton)
├── model_registry/                     # Versioned trained checkpoints (gitignored binaries)
└── requirements-ml.txt                 # torch/tensorflow/transformers/opencv — opt-in
```

---

## 📁 Project Folder Structure

```
canivue-api/
├── .gitignore                           # Excludes .agents/, virtualenvs, caches, model weights, etc.
├── requirements.txt                     # Production and development dependencies
├── requirements-ml.txt                  # Opt-in training deps: torch, transformers, opencv, scikit-learn...
├── pyproject.toml                       # Build & tool configurations (pytest, ruff, optional [ml] extra)
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
│       ├── sample/                      # Sample Feature Blueprint (plain CRUD)
│       │   ├── __init__.py
│       │   ├── domain/                  # 1. Pure Domain Logic & Interfaces
│       │   │   ├── __init__.py
│       │   │   ├── entities.py          # SampleItem entity
│       │   │   ├── exceptions.py        # Domain exceptions
│       │   │   └── repositories.py      # SampleRepositoryProtocol
│       │   ├── application/             # 2. Use Cases & DTOs
│       │   │   ├── __init__.py
│       │   │   ├── dtos.py              # Input/Output DTOs
│       │   │   └── use_cases.py         # Create/Get/List/Update/Delete Use Cases
│       │   ├── infrastructure/          # 3. Persistence & Adapters
│       │   │   ├── __init__.py
│       │   │   ├── models.py            # SampleModel (SQLAlchemy)
│       │   │   └── repositories.py      # SQLAlchemySampleRepository
│       │   └── presentation/            # 4. Delivery / Web API
│       │       ├── __init__.py
│       │       ├── schemas.py           # Request & Response Pydantic models
│       │       ├── dependencies.py      # Dependency Injection providers
│       │       └── router.py            # APIRouter endpoints
│       │
│       └── (future AI features go here, e.g. vision_diagnosis/, behavioural_analysis/, symptom_nlp/,
│            adaptive_fusion/, progression_risk/ -- same 4 layers + an infrastructure/ml/ sub-package,
│            see 🤖 AI/ML Architecture above and .agents/skills/ml-feature/SKILL.md)
│
├── ml/                                  # Offline training & evaluation -- NOT imported by app/ at runtime
│   ├── README.md                        # app/ vs ml/ split, rationale, layout
│   ├── common/
│   │   ├── data_splitting.py            # Dog-level train/val/test split (prevents leakage)
│   │   └── metrics.py                   # Accuracy/F1/ROC-AUC/Brier/ECE/temperature scaling
│   ├── vision/                          # Fully worked training example
│   │   ├── dataset.py, train.py, evaluate.py, README.md
│   ├── behavioural/                     # Skeleton -- same shape as vision/
│   │   ├── dataset.py, train.py, README.md
│   └── nlp/                             # Skeleton -- same shape as vision/
│       ├── dataset.py, train.py, README.md
│
├── model_registry/                      # Versioned trained checkpoints (binaries gitignored)
│   ├── README.md                        # Naming convention, why weights aren't committed
│   ├── vision/ behavioural/ nlp/
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

## ➕ Adding a New AI/ML Feature

Same steps as above, plus an `infrastructure/ml/` sub-package (`engine.py`
with a stub + real backend, `preprocessing.py` for input-quality checks) and
an `<X>InferenceEngineProtocol` in `domain/repositories.py`. Follow
[`.agents/skills/ml-feature/SKILL.md`](.agents/skills/ml-feature/SKILL.md)
step by step. Offline training code for the new model goes in `ml/<modality>/`,
not in `app/` — see [`ml/README.md`](ml/README.md).

---

## 🤖 Local Agent Skills (Untracked)

The local `.agents/skills/` directory provides workflow guides that assist development agents without polluting git history:
- `clean-architecture-feature`: Instructions and boilerplate rules for scaffolding new (non-ML) features.
- `ml-feature`: Instructions for scaffolding AI/ML inference features (vision, sensor, NLP, fusion, progression) using the same clean-architecture pattern.
- `standard-git-commit`: Guidelines for Conventional Commits.
