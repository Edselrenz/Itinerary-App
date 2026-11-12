"""Session, Credential, and Authentication State Management."""

import json
from pathlib import Path
from typing import Any, Callable, Optional

from desktop_client.config.settings import get_settings
from desktop_client.models.user import User


class SessionManager:
    """Manages active traveler authentication tokens and guest status."""

    def __init__(self):
        self.settings = get_settings()
        self.session_file = self.settings.storage_dir / "session.json"
        
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.current_user: Optional[User] = None
        self.is_guest: bool = False
        
        self._listeners: list[Callable[[], None]] = []
        self.load_session()

    def add_listener(self, callback: Callable[[], None]) -> None:
        """Subscribes a listener to session state changes (e.g. login/logout)."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self) -> None:
        for cb in self._listeners:
            try:
                cb()
            except Exception:
                pass

    @property
    def is_authenticated(self) -> bool:
        """Returns True if a valid access token and user session exist."""
        return bool(self.access_token and self.current_user and not self.is_guest)

    @property
    def display_name(self) -> str:
        """Formatted traveler name or Guest Traveler."""
        if self.is_guest:
            return "Guest Traveler"
        if self.current_user:
            return self.current_user.full_name or self.current_user.email
        return "Not Signed In"

    def set_authenticated_session(
        self,
        access_token: str,
        refresh_token: str,
        user: User,
        persist: bool = True,
    ) -> None:
        """Sets active traveler session and persists tokens to disk."""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.current_user = user
        self.is_guest = False

        if persist:
            self._save_to_disk()
        self._notify()

    def set_guest_mode(self) -> None:
        """Enables local guest mode without backend credentials."""
        self.access_token = None
        self.refresh_token = None
        self.current_user = None
        self.is_guest = True
        self._clear_disk()
        self._notify()

    def clear_session(self) -> None:
        """Completely logs out the user and clears in-memory state."""
        self.access_token = None
        self.refresh_token = None
        self.current_user = None
        self.is_guest = False
        self._clear_disk()
        self._notify()

    def get_access_token(self) -> Optional[str]:
        return self.access_token

    def get_refresh_token(self) -> Optional[str]:
        return self.refresh_token

    def update_user(self, user: User) -> None:
        """Updates cached user entity and persists."""
        self.current_user = user
        if self.access_token:
            self._save_to_disk()
        self._notify()

    def load_session(self) -> bool:
        """Restores persisted credentials from local disk if available."""
        if not self.session_file.exists():
            return False
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            user_data = data.get("user")
            if user_data:
                self.current_user = User.from_dict(user_data)
            self.is_guest = bool(data.get("is_guest", False))
            return True
        except Exception:
            return False

    def _save_to_disk(self) -> None:
        try:
            data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "user": self.current_user.to_dict() if self.current_user else None,
                "is_guest": self.is_guest,
            }
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _clear_disk(self) -> None:
        try:
            if self.session_file.exists():
                self.session_file.unlink()
        except Exception:
            pass


_session_manager_instance: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Singleton getter for SessionManager."""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
    return _session_manager_instance
