"""FastAPI entry point for the Nueva Ecija Travel Itinerary API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.itineraries import router as itineraries_router
from app.api.v1.places import router as places_router
from app.core.config import settings

app = FastAPI(
    title="Nueva Ecija Travel Itinerary API",
    version="0.1.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(places_router, prefix=settings.api_v1_prefix)
app.include_router(itineraries_router, prefix=settings.api_v1_prefix)


@app.get(f"{settings.api_v1_prefix}/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Liveness health check verifying API availability without leaking secrets."""
    return {
        "status": "ok",
        "province_scope": "Nueva Ecija",
        "environment": settings.app_env,
    }
