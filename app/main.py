import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import Base, engine
from app.core.exception_handlers.app_exception_handler import (
    app_exception_handler,
)
from app.core.exception_handlers.generic_exception_handler import (
    generic_exception_handler,
)
from app.core.exceptions import AppException
from app.core.middlewares.logging_middleware import LoggingMiddleware
from app.core.response import APIResponse


async def seed_reference_data() -> None:
    """Idempotently adds the rows the app cannot work without: permissions and communities."""
    from app.core.database import AsyncSessionLocal
    from app.features.auth.infrastructure.persistence.seed import seed_rbac_catalog
    from app.features.community.infrastructure.persistence.seed import seed_communities

    async with AsyncSessionLocal() as session:
        await seed_rbac_catalog(session)
        await seed_communities(session)
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan event handler."""
    # Startup: Auto-create database tables in development mode
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_reference_data()

    # Pre-warm real ML engines on startup if configured (lifespan eager loading)
    if settings.USE_REAL_ML_MODELS:
        from app.features.symptom_nlp.presentation.dependencies import get_symptom_engine

        get_symptom_engine()

    yield
    # Shutdown: Dispose engine connection pool
    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory initializing FastAPI, middlewares, and routes."""
    # Without this the app's own INFO logs (request lifecycle, the development email
    # service that prints verification codes and reset tokens) are silently dropped.
    logging.basicConfig(
        level=logging.INFO if settings.DEBUG else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="FastAPI Modular Monolith with Feature-Based Clean Architecture",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # Request / Response Lifecycle Logging Middleware
    app.add_middleware(LoggingMiddleware)

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Base Health Check Endpoint
    @app.get("/health", response_model=APIResponse[dict], tags=["System"])
    async def health_check() -> APIResponse[dict]:
        return APIResponse(
            success=True,
            message="Service is running healthy",
            data={"status": "healthy", "environment": settings.APP_ENV},
        )

    # Register Feature Routers

    from app.features.auth.presentation.router import router as auth_router

    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication & RBAC"])

    from app.features.dogs.presentation.router import router as dogs_router

    app.include_router(dogs_router, prefix="/api/v1/dogs", tags=["Dogs"])

    from app.features.veterinarians.presentation.router import router as veterinarians_router

    app.include_router(veterinarians_router, prefix="/api/v1/veterinarians", tags=["Veterinarians"])

    from app.features.appointments.presentation.router import dog_router as dog_appointments_router
    from app.features.appointments.presentation.router import router as appointments_router

    app.include_router(dog_appointments_router, prefix="/api/v1/dogs", tags=["Appointments"])
    app.include_router(appointments_router, prefix="/api/v1/appointments", tags=["Appointments"])

    from app.features.notifications.presentation.router import router as notifications_router

    app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["Notifications"])

    from app.features.messaging.presentation.router import router as messaging_router

    app.include_router(messaging_router, prefix="/api/v1/conversations", tags=["Messaging"])

    from app.features.medical_records.presentation.router import router as medical_records_router

    app.include_router(medical_records_router, prefix="/api/v1/dogs", tags=["Medical Records"])

    from app.features.preventive_care.presentation.router import router as preventive_care_router

    app.include_router(preventive_care_router, prefix="/api/v1/dogs", tags=["Preventive Care"])

    from app.features.devices.presentation.router import router as devices_router

    app.include_router(devices_router, prefix="/api/v1/dogs", tags=["Devices"])

    from app.features.health_metrics.presentation.router import router as health_metrics_router

    app.include_router(health_metrics_router, prefix="/api/v1/dogs", tags=["Health Metrics"])

    from app.features.nutrition.presentation.router import router as nutrition_router

    app.include_router(nutrition_router, prefix="/api/v1/dogs", tags=["Nutrition"])

    from app.features.assessments.presentation.router import router as assessments_router

    app.include_router(assessments_router, prefix="/api/v1/dogs", tags=["Assessments"])

    from app.features.dashboard.presentation.router import router as dashboard_router

    app.include_router(dashboard_router, prefix="/api/v1/dogs", tags=["Dashboard"])

    from app.features.community.presentation.router import router as community_router

    app.include_router(community_router, prefix="/api/v1/community", tags=["Community"])

    from app.features.billing.presentation.router import router as billing_router

    app.include_router(billing_router, prefix="/api/v1/billing", tags=["Billing"])

    from app.features.reviews.presentation.router import router as reviews_router

    app.include_router(reviews_router, prefix="/api/v1", tags=["Reviews"])

    from app.features.vet_portal.presentation.router import router as vet_portal_router

    app.include_router(vet_portal_router, prefix="/api/v1/vet-portal", tags=["Veterinarian Portal"])

    from app.features.symptom_nlp.presentation.router import router as symptom_nlp_router

    app.include_router(symptom_nlp_router, prefix="/api/v1/symptoms", tags=["Symptoms NLP"])

    # Mount Clinical Inspector & Active Learning Studio in development
    if settings.DEBUG:
        try:
            from tools.nlp_inspector.app import app as inspector_app

            app.mount("/inspector", inspector_app)
        except Exception:
            pass

    return app


app = create_app()
