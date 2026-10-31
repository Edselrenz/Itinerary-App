"""FastAPI entry point for the Nueva Ecija Travel Itinerary API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.itineraries import router as itineraries_router
from app.api.v1.places import router as places_router
from app.core.config import settings
from app.core.limiter import limiter

app = FastAPI(
    title="Nueva Ecija Travel Itinerary API",
    version="0.1.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
)

# SlowAPI rate limiting configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https://.*\.github\.io$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
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
