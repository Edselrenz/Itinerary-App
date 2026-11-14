"""Authentication Service handling traveler registration, sign-in, token refresh, and guest mode."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from desktop_client.config.settings import get_settings
from desktop_client.core.api_client import (
    ApiClient,
    ApiClientError,
    AuthenticationError,
    NetworkError,
    get_api_client,
)
from desktop_client.core.session import SessionManager, get_session_manager
from desktop_client.models.user import AuthTokenResponse, User, UserUpdatePayload


class AuthService:
    """Handles all user identity, login sessions, credential persistence, and extended profile storage."""

    def __init__(
        self,
        api_client: Optional[ApiClient] = None,
        session_manager: Optional[SessionManager] = None,
    ):
        self.settings = get_settings()
        self.api_client = api_client or get_api_client()
        self.session_manager = session_manager or get_session_manager()

        # Wire session tokens into API client
        self.api_client.set_token_getter(self.session_manager.get_access_token)
        self.api_client.set_refresh_handler(self.refresh_token)

    def _load_profile_extra(self, user_id: str) -> dict[str, Any]:
        """Loads extended profile metadata (middle_initial, birthday, gender, etc.) from local storage."""
        file_path = self.settings.storage_dir / "profile_extra.json"
        if not file_path.exists():
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                all_extra = json.load(f)
                return all_extra.get(user_id, {})
        except Exception:
            return {}

    def _save_profile_extra(self, user_id: str, extra_data: dict[str, Any]) -> None:
        """Persists extended profile metadata locally in profile_extra.json."""
        file_path = self.settings.storage_dir / "profile_extra.json"
        all_extra: dict[str, Any] = {}
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    all_extra = json.load(f)
            except Exception:
                all_extra = {}

        existing = all_extra.get(user_id, {})
        existing.update({k: v for k, v in extra_data.items() if v is not None})
        all_extra[user_id] = existing

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(all_extra, f, indent=2)
        except Exception:
            pass

    async def login(self, email: str, password: str, remember_me: bool = True) -> User:
        """Authenticates traveler with email and password."""
        payload = {"email": email.strip(), "password": password}
        data = await self.api_client.post("auth/login", json_data=payload)

        token_resp = AuthTokenResponse.from_dict(data)
        user = token_resp.user or User(id="", email=email)

        self.session_manager.set_authenticated_session(
            access_token=token_resp.access_token,
            refresh_token=token_resp.refresh_token,
            user=user,
            persist=remember_me,
        )

        try:
            me_user = await self.get_profile()
            if me_user:
                user = me_user
        except Exception:
            user_id = user.id
            if user_id:
                extra = self._load_profile_extra(user_id)
                if extra:
                    user = User.from_dict(user.to_dict(), extra=extra)
                    self.session_manager.update_user(user)

        return user

    async def register(
        self,
        email: str,
        password: str,
        full_name: str = "",
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        middle_initial: Optional[str] = None,
    ) -> User:
        """Registers a new traveler account strictly adhering to backend UserRegisterIn schema."""
        email_clean = email.strip()
        first = (first_name or "").strip()
        last = (last_name or "").strip()
        if not first and full_name:
            parts = full_name.strip().split(maxsplit=1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else parts[0]
        if not first:
            first = email_clean.split("@")[0] or "Traveler"
        if not last:
            last = "Explorer"

        uname = (username or "").strip()
        if not uname:
            base_uname = email_clean.split("@")[0].replace(".", "_").replace("-", "_")
            uname = base_uname if len(base_uname) >= 3 else f"{base_uname}123"

        payload = {
            "first_name": first,
            "last_name": last,
            "username": uname,
            "email": email_clean,
            "password": password,
        }
        data = await self.api_client.post("auth/register", json_data=payload)
        token_resp = AuthTokenResponse.from_dict(data)

        user_id = str(data.get("id") or (token_resp.user.id if token_resp.user else ""))
        if middle_initial:
            self._save_profile_extra(user_id, {"middle_initial": middle_initial.strip()})

        extra = self._load_profile_extra(user_id)
        if not token_resp.user:
            user = User(
                id=user_id,
                email=email_clean,
                first_name=first,
                last_name=last,
                middle_initial=str(middle_initial or "").strip(),
                username=uname,
            )
            self.session_manager.set_authenticated_session(
                access_token=token_resp.access_token,
                refresh_token=token_resp.refresh_token,
                user=user,
                persist=True,
            )
            return user

        if extra:
            token_resp.user = User.from_dict(token_resp.user.to_dict(), extra=extra)

        self.session_manager.set_authenticated_session(
            access_token=token_resp.access_token,
            refresh_token=token_resp.refresh_token,
            user=token_resp.user,
            persist=True,
        )
        return token_resp.user

    async def refresh_token(self) -> bool:
        """Exchanges refresh token for a fresh token pair."""
        refresh = self.session_manager.get_refresh_token()
        if not refresh:
            return False

        try:
            payload = {"refresh_token": refresh}
            data = await self.api_client.post("auth/refresh", json_data=payload)
            token_resp = AuthTokenResponse.from_dict(data)

            user = self.session_manager.current_user or token_resp.user
            if not user:
                user = User(id="", email="")

            self.session_manager.set_authenticated_session(
                access_token=token_resp.access_token,
                refresh_token=token_resp.refresh_token,
                user=user,
                persist=True,
            )
            return True
        except Exception:
            self.session_manager.clear_session()
            return False

    async def get_profile(self) -> User:
        """Fetches current user profile from backend and merges local extended profile metadata."""
        if not self.session_manager.is_authenticated:
            current = self.session_manager.current_user
            if not current:
                extra = self._load_profile_extra("guest-local")
                current = User.create_guest(extra=extra)
                self.session_manager.current_user = current
            return current

        try:
            data = await self.api_client.get("auth/me")
            user_id = str(data.get("id", ""))
            extra = self._load_profile_extra(user_id)
            user = User.from_dict(data, extra=extra)
            # Persist fresh profile metadata to local cache
            db_profile_extra = {
                "middle_initial": user.middle_initial,
                "phone_number": user.phone_number,
                "birthday": user.birthday,
                "gender": user.gender,
                "avatar_url": user.avatar_url,
                "default_daily_budget": user.default_daily_budget,
            }
            self._save_profile_extra(user_id, db_profile_extra)
            self.session_manager.update_user(user)
            return user
        except Exception:
            # Offline fallback
            current = self.session_manager.current_user
            if current:
                extra = self._load_profile_extra(current.id)
                current = User.from_dict(current.to_dict(), extra=extra)
                self.session_manager.update_user(current)
                return current
            raise

    async def update_profile(self, payload: UserUpdatePayload) -> User:
        """Updates user profile attributes across FastAPI PATCH /api/v1/auth/me and local profile_extra."""
        current = self.session_manager.current_user
        user_id = current.id if current and current.id else ("guest-local" if self.session_manager.is_guest else "guest-local")

        # 1. Persist extended profile metadata locally
        extra = payload.to_extra_dict()
        if extra:
            self._save_profile_extra(user_id, extra)
        saved_extra = self._load_profile_extra(user_id)

        # 2. Authenticated online sync
        if self.session_manager.is_authenticated and not getattr(current, "is_guest", False):
            backend_payload = payload.to_backend_dict()
            if backend_payload:
                try:
                    data = await self.api_client.patch("auth/me", json_data=backend_payload)
                    user = User.from_dict(data, extra=saved_extra)
                    self.session_manager.update_user(user)
                    return user
                except (ApiClientError, NetworkError, Exception):
                    # Graceful offline fallback: update local user object
                    pass

        # 3. Guest or offline update
        base_dict = current.to_dict() if current else {}
        for k, v in extra.items():
            if v is not None:
                base_dict[k] = v
        if payload.first_name:
            base_dict["first_name"] = payload.first_name.strip()
        if payload.last_name:
            base_dict["last_name"] = payload.last_name.strip()
        if payload.username:
            base_dict["username"] = payload.username.strip()

        user = User.from_dict(base_dict, extra=saved_extra)
        if self.session_manager.is_guest:
            user.is_guest = True
            user.role = "guest"

        self.session_manager.update_user(user)
        return user

    def continue_as_guest(self) -> None:
        """Switches session into Guest Mode with local extended profile metadata."""
        extra = self._load_profile_extra("guest-local")
        self.session_manager.set_guest_mode()
        self.session_manager.current_user = User.create_guest(extra=extra)
        self.session_manager._save_to_disk()
        self.session_manager._notify()

    def logout(self) -> None:
        """Logs out traveler and clears tokens."""
        self.session_manager.clear_session()

    async def migrate_guest_trips(self) -> int:
        """Migrates local guest itineraries into the authenticated traveler account."""
        from desktop_client.core.storage import get_guest_storage
        from desktop_client.services.itinerary_service import get_itinerary_service

        storage = get_guest_storage()
        itins = storage.list_itineraries()
        if not itins:
            return 0

        itin_service = get_itinerary_service()
        migrated = 0
        for it in itins:
            try:
                payload = it.to_create_payload()
                await itin_service.create_itinerary(payload)
                storage.delete_itinerary(it.id)
                migrated += 1
            except Exception:
                continue
        return migrated


_auth_service_instance: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Singleton getter for AuthService."""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService()
    return _auth_service_instance
