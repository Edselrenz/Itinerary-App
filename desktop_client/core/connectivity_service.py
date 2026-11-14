"""Global Connectivity Service and Backend Health Telemetry.

Ported from Project/src/app/core/services/connectivity.service.ts.
Manages online/offline state, consecutive error thresholds, custom API URL overrides,
and asynchronous /health endpoint probing.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Callable, Optional
import urllib.parse

import httpx

from desktop_client.config.settings import get_settings


class ConnectivityService:
    _instance: Optional[ConnectivityService] = None

    def __init__(self) -> None:
        self.settings = get_settings()
        self._is_host_offline: bool = False
        self._is_checking_health: bool = False
        self._is_dismissed_manually: bool = False
        self._consecutive_errors: int = 0
        self.ERROR_THRESHOLD: int = 2

        self._listeners: list[Callable[[], None]] = []
        self._storage_file = Path(self.settings.storage_dir) / "connectivity_settings.json"
        self._custom_api_url: Optional[str] = self._load_custom_api_url()

    @classmethod
    def get_instance(cls) -> ConnectivityService:
        if cls._instance is None:
            cls._instance = ConnectivityService()
        return cls._instance

    @property
    def is_host_offline(self) -> bool:
        return self._is_host_offline and not self._is_dismissed_manually

    @property
    def is_host_offline_raw(self) -> bool:
        return self._is_host_offline

    @property
    def is_checking_health(self) -> bool:
        return self._is_checking_health

    @property
    def consecutive_error_count(self) -> int:
        return self._consecutive_errors

    @property
    def is_dismissed_manually(self) -> bool:
        return self._is_dismissed_manually

    @property
    def active_api_base_url(self) -> str:
        if self._custom_api_url and self.is_valid_api_url(self._custom_api_url):
            return self._custom_api_url
        return self.settings.api_base_url

    @property
    def current_api_url(self) -> str:
        return self.active_api_base_url

    def add_listener(self, callback: Callable[..., None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def register_listener(self, callback: Callable[..., None]) -> None:
        """Alias for add_listener."""
        self.add_listener(callback)

    def remove_listener(self, callback: Callable[..., None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self) -> None:
        for cb in list(self._listeners):
            try:
                import inspect
                sig = inspect.signature(cb)
                if len(sig.parameters) > 0:
                    cb(self.is_host_offline)
                else:
                    cb()
            except Exception:
                try:
                    cb()
                except Exception:
                    pass

    def report_gateway_error(self) -> None:
        self._consecutive_errors += 1
        if self._consecutive_errors >= self.ERROR_THRESHOLD:
            if not self._is_dismissed_manually:
                self._is_host_offline = True
                self._notify_listeners()

    def set_host_offline(self, is_offline: bool, force: bool = False) -> None:
        if is_offline:
            if force:
                self._consecutive_errors = self.ERROR_THRESHOLD
                self._is_dismissed_manually = False
                self._is_host_offline = True
                self._notify_listeners()
            else:
                self.report_gateway_error()
        else:
            self._consecutive_errors = 0
            self._is_dismissed_manually = False
            self._is_host_offline = False
            self._notify_listeners()

    def dismiss_banner(self) -> None:
        self._is_dismissed_manually = True
        self._notify_listeners()

    def is_valid_api_url(self, url: str) -> bool:
        if not url or not isinstance(url, str):
            return False
        try:
            parsed = urllib.parse.urlparse(url.strip())
            hostname = (parsed.hostname or "").lower()

            is_trusted_host = (
                hostname in ("localhost", "127.0.0.1", "anybody-cube-surprise.ngrok-free.dev")
                or hostname.endswith(".ngrok-free.dev")
                or hostname.endswith(".ngrok.app")
                or hostname.endswith(".ngrok.io")
                or hostname.endswith(".trycloudflare.com")
                or hostname.endswith(".workers.dev")
                or hostname.endswith(".onrender.com")
                or hostname.endswith(".koyeb.app")
            )

            if not is_trusted_host:
                return False

            if parsed.scheme == "https":
                return True
            if parsed.scheme == "http" and hostname in ("localhost", "127.0.0.1"):
                return True
            return False
        except Exception:
            return False

    def set_custom_api_url(self, url: Optional[str]) -> bool:
        if url and url.strip():
            trimmed = url.strip().rstrip("/")
            if not self.is_valid_api_url(trimmed):
                raise ValueError("Invalid API URL: Must use trusted host with https:// or http://localhost.")
            if not trimmed.endswith("/api/v1"):
                trimmed = f"{trimmed}/api/v1"
            self._custom_api_url = trimmed
        else:
            self._custom_api_url = None

        self._save_custom_api_url(self._custom_api_url)
        self._is_dismissed_manually = False
        self._notify_listeners()
        return True

    def clear_custom_api_url(self) -> None:
        self._custom_api_url = None
        self._save_custom_api_url(None)
        self._is_dismissed_manually = False
        self._notify_listeners()

    def _load_custom_api_url(self) -> Optional[str]:
        if not self._storage_file.exists():
            return None
        try:
            with open(self._storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("ne_custom_api_url")
        except Exception:
            return None

    def _save_custom_api_url(self, url: Optional[str]) -> None:
        try:
            os.makedirs(self._storage_file.parent, exist_ok=True)
            with open(self._storage_file, "w", encoding="utf-8") as f:
                json.dump({"ne_custom_api_url": url}, f, indent=2)
        except Exception:
            pass

    CLOUDFLARE_WORKER_API_URL: str = "https://ne-itinerary-api.edselrenz0.workers.dev/api/v1"

    async def check_host_health(self) -> bool:
        self._is_checking_health = True
        self._notify_listeners()

        req_headers = {"ngrok-skip-browser-warning": "true", "Accept": "application/json"}
        health_url = f"{self.active_api_base_url}/health"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(health_url, headers=req_headers)
                if res.status_code == 200:
                    self._is_checking_health = False
                    self.set_host_offline(False)
                    return True
        except Exception:
            pass

        # If default localhost is down and no custom URL is set, try Cloudflare Worker proxy
        if not self._custom_api_url and "127.0.0.1" in self.settings.api_base_url:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    cf_res = await client.get(f"{self.CLOUDFLARE_WORKER_API_URL}/health", headers=req_headers)
                    if cf_res.status_code == 200:
                        self.settings.api_base_url = self.CLOUDFLARE_WORKER_API_URL
                        self._is_checking_health = False
                        self.set_host_offline(False)
                        return True
            except Exception:
                pass

        self._is_checking_health = False
        self.set_host_offline(True, force=True)
        return False

    def check_host_health_sync(self) -> bool:
        health_url = f"{self.active_api_base_url}/health"
        req_headers = {"ngrok-skip-browser-warning": "true", "Accept": "application/json"}
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(health_url, headers=req_headers)
                if res.status_code == 200:
                    self.set_host_offline(False)
                    return True
                else:
                    self.set_host_offline(True, force=True)
                    return False
        except Exception:
            self.set_host_offline(True, force=True)
            return False


def get_connectivity_service() -> ConnectivityService:
    return ConnectivityService.get_instance()
