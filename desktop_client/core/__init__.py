"""Core infrastructure for Nueva Ecija Travel Desktop Client."""

from desktop_client.core.api_client import (
    ApiClient,
    ApiClientError,
    AuthenticationError,
    NotFoundError,
    NetworkError,
    get_api_client,
)
from desktop_client.core.session import SessionManager, get_session_manager
from desktop_client.core.storage import GuestStorageManager, get_guest_storage
from desktop_client.core.export import export_to_ics, export_to_text, export_to_json

__all__ = [
    "ApiClient",
    "ApiClientError",
    "AuthenticationError",
    "NotFoundError",
    "NetworkError",
    "get_api_client",
    "SessionManager",
    "get_session_manager",
    "GuestStorageManager",
    "get_guest_storage",
    "export_to_ics",
    "export_to_text",
    "export_to_json",
]
