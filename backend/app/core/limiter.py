"""Rate limiting configuration using SlowAPI for the Nueva Ecija Travel Itinerary API."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Global limiter instance keyed by remote IP address
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    headers_enabled=False,
)
