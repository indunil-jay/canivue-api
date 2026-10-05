# 0001. Modular Monolith and Clean Architecture

We have decided to organize the Canivue backend as a **Modular Monolith** with **Feature-Based Clean Architecture** in FastAPI.

## Context
Canivue requires complex multi-modal AI capabilities (vision, behavioural sensors, symptom NLP, fusion, disease progression) alongside traditional relational business entities (dogs, users, clinics). Splitting into separate microservices early introduces substantial deployment, network, and operational overhead. Conversely, a typical flat MVC web app leads to high coupling between ORM models, frameworks, and ML dependencies.

## Decision
1. **Modular Monolith**: All features live in a single repository and deployable backend unit under `app/features/<feature>/`.
2. **Strict Inward Dependency Rule**: Each feature module enforces 4 clean-architecture layers:
   - `Presentation`: FastAPI routers, Pydantic schemas, dependency injection.
   - `Application`: Use Cases and DTOs.
   - `Domain`: Pure Python entities, domain exceptions, and repository protocols. Zero framework dependencies.
   - `Infrastructure`: SQLAlchemy models, persistence repositories, and ML engine adapters.
3. **AI/ML Behind Domain Protocols**: ML inference engines implement `<X>InferenceEngineProtocol`. PyTorch and heavy ML libraries are restricted to `infrastructure/ml/` and offline training in `ml/`.

## Consequences
- Fast unit test execution using zero-dependency stub engines without GPU requirements.
- Strong decoupling: features can be migrated to independent microservices in the future if scale demands it with minimal refactoring.
