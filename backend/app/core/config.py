"""Application configuration loaded from environment variables."""

from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Validated backend configuration for the Nueva Ecija Travel Itinerary API."""

    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = (
        "postgresql+psycopg://ne_travel_user:change_me_local_only@127.0.0.1:5432/nueva_ecija_travel"
    )
    jwt_secret_key: str = "dev_only_replace_before_pilot_with_openssl_rand_hex_32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: list[str] = [
        "http://localhost:8100",
        "http://localhost:4200",
        "capacitor://localhost",
        "http://localhost",
        "https://edselrenz.github.io",
    ]
    cors_origin_regex: str | None = r"^https://edselrenz\.github\.io$"
    google_oauth_client_id: str = ""
    enable_apple_auth: bool = False
    default_dest_radius_km: float = 25.0
    google_maps_api_key: str = ""
    google_places_cache_ttl_hours: int = 168  # 7 days for discovery
    google_details_cache_ttl_hours: int = 24  # 24 hours for rich reviews/photos
    google_routes_cache_ttl_hours: int = 336  # 14 days for routes

    @model_validator(mode="after")
    def validate_secrets(self) -> "Settings":
        if self.app_env != "development":
            insecure_defaults = {
                "dev_only_replace_before_pilot_with_openssl_rand_hex_32",
                "change-this-in-production-use-openssl-rand-hex-32",
                "secret",
                "changeme",
            }
            if (
                not self.jwt_secret_key
                or self.jwt_secret_key.strip() in insecure_defaults
                or len(self.jwt_secret_key.strip()) < 32
            ):
                raise ValueError(
                    "jwt_secret_key must be explicitly configured outside development environment."
                )
        return self

    model_config = SettingsConfigDict(
        env_file=(str(ROOT_ENV), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
