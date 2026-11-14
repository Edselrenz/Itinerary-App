"""Asynchronous HTTP Client for Nueva Ecija Travel API."""

import asyncio
from typing import Any, Optional
import httpx

from desktop_client.config.settings import get_settings


class ApiClientError(Exception):
    """Base exception for all API client errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class AuthenticationError(ApiClientError):
    """Raised when authentication fails (HTTP 401 or 403)."""
    pass


class NotFoundError(ApiClientError):
    """Raised when the requested resource is not found (HTTP 404)."""
    pass


class ValidationError(ApiClientError):
    """Raised when request payload fails schema validation (HTTP 422)."""
    pass


class NetworkError(ApiClientError):
    """Raised when network connectivity fails or requests time out."""
    pass


class ApiClient:
    """Robust Async HTTP Client managing connections, authorization headers, and error handling."""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        settings = get_settings()
        self._explicit_base_url: Optional[str] = base_url.rstrip("/") if base_url else None
        self.default_timeout = timeout or settings.api_timeout_seconds
        self._token_getter = None
        self._refresh_handler = None
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def base_url(self) -> str:
        if self._explicit_base_url:
            return self._explicit_base_url
        try:
            from desktop_client.core.connectivity_service import get_connectivity_service
            return get_connectivity_service().active_api_base_url.rstrip("/")
        except Exception:
            return get_settings().api_base_url.rstrip("/")

    @base_url.setter
    def base_url(self, val: str) -> None:
        self._explicit_base_url = val.rstrip("/") if val else None

    def set_token_getter(self, getter_func):
        """Sets a callback that provides the current Bearer access token."""
        self._token_getter = getter_func

    def set_refresh_handler(self, refresh_func):
        """Sets a callback that performs a token refresh when 401 is encountered."""
        self._refresh_handler = refresh_func

    def _get_headers(self, custom_headers: Optional[dict[str, str]] = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "NuevaEcijaTravel-Desktop/1.0.0",
        }
        if self._token_getter:
            token = self._token_getter()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        if custom_headers:
            headers.update(custom_headers)
        return headers

    async def get_client(self) -> httpx.AsyncClient:
        """Returns or creates the underlying httpx.AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.default_timeout, connect=5.0),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Closes the client session cleanly."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def check_health_sync(self) -> bool:
        """Synchronous fast socket check of backend availability dynamically probing configured host/port."""
        try:
            import socket
            from urllib.parse import urlparse

            parsed = urlparse(self.base_url)
            host = parsed.hostname or "127.0.0.1"
            if parsed.port:
                port = parsed.port
            elif parsed.scheme == "https":
                port = 443
            else:
                port = 80

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            err = sock.connect_ex((host, port))
            sock.close()
            return err == 0
        except Exception:
            return False

    async def check_health(self) -> bool:
        """Pings the backend to verify service availability with fast probe."""
        return await asyncio.to_thread(self.check_health_sync)

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
        retried: bool = False,
    ) -> Any:
        """Executes an HTTP request with error handling and automatic retry on 401."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        req_headers = self._get_headers(headers)
        req_timeout = timeout or self.default_timeout
        client = await self.get_client()

        try:
            response = await client.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_data,
                headers=req_headers,
                timeout=req_timeout,
            )
            try:
                from desktop_client.core.connectivity_service import get_connectivity_service
                get_connectivity_service().set_host_offline(False)
            except Exception:
                pass
        except httpx.ConnectError as err:
            try:
                from desktop_client.core.connectivity_service import get_connectivity_service
                get_connectivity_service().set_host_offline(True, force=True)
            except Exception:
                pass
            raise NetworkError(f"Cannot connect to server at {self.base_url}. Please check if backend is running.") from err
        except httpx.TimeoutException as err:
            try:
                from desktop_client.core.connectivity_service import get_connectivity_service
                get_connectivity_service().report_gateway_error()
            except Exception:
                pass
            raise NetworkError(f"Request to {endpoint} timed out after {req_timeout}s.") from err
        except httpx.RequestError as err:
            try:
                from desktop_client.core.connectivity_service import get_connectivity_service
                get_connectivity_service().report_gateway_error()
            except Exception:
                pass
            raise NetworkError(f"Network error: {str(err)}") from err

        # Handle 401 Token Expiry with single automatic refresh retry
        if response.status_code == 401 and not retried and self._refresh_handler:
            refreshed = await self._refresh_handler()
            if refreshed:
                return await self.request(
                    method=method,
                    endpoint=endpoint,
                    params=params,
                    json_data=json_data,
                    headers=headers,
                    timeout=timeout,
                    retried=True,
                )

        if response.status_code == 401 or response.status_code == 403:
            detail = self._extract_error_detail(response)
            raise AuthenticationError(detail, status_code=response.status_code)

        if response.status_code == 404:
            detail = self._extract_error_detail(response)
            raise NotFoundError(detail, status_code=404)

        if response.status_code == 422:
            detail = self._extract_error_detail(response)
            raise ValidationError(detail, status_code=422, details=response.json() if self._is_json(response) else None)

        if response.is_error:
            detail = self._extract_error_detail(response)
            raise ApiClientError(f"API Error ({response.status_code}): {detail}", status_code=response.status_code)

        if response.status_code == 204 or not response.content:
            return None

        if self._is_json(response):
            return response.json()
        return response.text

    @staticmethod
    def _is_json(response: httpx.Response) -> bool:
        return "application/json" in response.headers.get("Content-Type", "")

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            data = response.json()
            if isinstance(data, dict):
                return data.get("detail", data.get("message", response.text))
            return str(data)
        except Exception:
            return response.text or f"HTTP status {response.status_code}"

    # Convenience HTTP verbs
    async def get(self, endpoint: str, params: Optional[dict[str, Any]] = None, **kwargs) -> Any:
        return await self.request("GET", endpoint, params=params, **kwargs)

    async def post(self, endpoint: str, json_data: Optional[Any] = None, **kwargs) -> Any:
        return await self.request("POST", endpoint, json_data=json_data, **kwargs)

    async def put(self, endpoint: str, json_data: Optional[Any] = None, **kwargs) -> Any:
        return await self.request("PUT", endpoint, json_data=json_data, **kwargs)

    async def patch(self, endpoint: str, json_data: Optional[Any] = None, **kwargs) -> Any:
        return await self.request("PATCH", endpoint, json_data=json_data, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Any:
        return await self.request("DELETE", endpoint, **kwargs)


_api_client_instance: Optional[ApiClient] = None


def get_api_client() -> ApiClient:
    """Singleton getter for ApiClient."""
    global _api_client_instance
    if _api_client_instance is None:
        _api_client_instance = ApiClient()
    return _api_client_instance
