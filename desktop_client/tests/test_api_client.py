"""Unit tests for ApiClient."""

import pytest
import httpx
from desktop_client.core.api_client import (
    ApiClient,
    ApiClientError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    NetworkError,
)


def test_api_client_initialization():
    client = ApiClient(base_url="http://localhost:8000/api/v1", timeout=10.0)
    assert client.base_url == "http://localhost:8000/api/v1"
    assert client.default_timeout == 10.0


def test_api_client_token_injection():
    client = ApiClient()
    client.set_token_getter(lambda: "test-jwt-token-123")
    headers = client._get_headers()
    assert headers["Authorization"] == "Bearer test-jwt-token-123"
    assert headers["Accept"] == "application/json"


def test_api_client_custom_headers():
    client = ApiClient()
    headers = client._get_headers({"X-Custom-Header": "CustomValue"})
    assert headers["X-Custom-Header"] == "CustomValue"


def test_exception_hierarchy():
    auth_err = AuthenticationError("Unauthorized", status_code=401)
    not_found = NotFoundError("Not Found", status_code=404)
    val_err = ValidationError("Invalid field", status_code=422)
    net_err = NetworkError("Connection refused")

    assert isinstance(auth_err, ApiClientError)
    assert isinstance(not_found, ApiClientError)
    assert isinstance(val_err, ApiClientError)
    assert isinstance(net_err, ApiClientError)
    assert auth_err.status_code == 401
    assert not_found.status_code == 404
    assert val_err.status_code == 422
