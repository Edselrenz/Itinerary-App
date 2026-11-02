"""Rate limiting configuration using SlowAPI for the Nueva Ecija Travel Itinerary API."""

"""Rate limiting configuration using SlowAPI for the Nueva Ecija Travel Itinerary API."""

from starlette.requests import Request
from slowapi import Limiter


def get_client_ip(request: Request) -> str:
    """Resolve the real client IP address, supporting Cloudflare Tunnel and reverse proxies.

    When running behind Cloudflare Tunnel (cloudflared) or a local reverse proxy,
    the direct socket host is typically 127.0.0.1, localhost, or ::1. In that case,
    extract the authenticated client IP from CF-Connecting-IP or X-Forwarded-For.
    Direct remote connections use the direct socket client IP to prevent header spoofing.
    """
    client_host = request.client.host if request.client else "127.0.0.1"

    if client_host in ("127.0.0.1", "localhost", "::1", "testclient"):
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip and cf_ip.strip():
            return cf_ip.strip()

        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for and x_forwarded_for.strip():
            # First IP in comma-separated chain is the originating client IP
            return x_forwarded_for.split(",")[0].strip()

    return client_host


# Global limiter instance keyed by resolved client IP address
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["120/minute"],
    headers_enabled=False,
)
