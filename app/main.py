from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import Base, engine
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
)
from app.core.response import APIResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan event handler."""
    # Startup: Auto-create database tables in development mode
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Dispose engine connection pool
    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory initializing FastAPI, middlewares, and routes."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="FastAPI Modular Monolith with Feature-Based Clean Architecture",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

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
    from app.features.sample.presentation.router import router as sample_router
    app.include_router(sample_router, prefix="/api/v1/samples", tags=["Sample Feature"])

    from app.features.symptom_nlp.presentation.router import router as symptom_nlp_router
    app.include_router(symptom_nlp_router, prefix="/api/v1/symptoms", tags=["Symptoms NLP"])

    return app


app = create_app()
