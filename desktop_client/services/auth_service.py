"""Authentication Service handling traveler registration, sign-in, token refresh, and guest mode."""

from typing import Any, Optional

from desktop_client.core.api_client import (
    ApiClient,
    AuthenticationError,
    get_api_client,
)
from desktop_client.core.session import SessionManager, get_session_manager
from desktop_client.models.user import AuthTokenResponse, User, UserUpdatePayload


class AuthService:
    """Handles all user identity, login sessions, and credential persistence."""

    def __init__(self, api_client: Optional[ApiClient] = None, session_manager: Optional[SessionManager] = None):
        self.api_client = api_client or get_api_client()
        self.session_manager = session_manager or get_session_manager()

        # Wire session tokens into API client
        self.api_client.set_token_getter(self.session_manager.get_access_token)
        self.api_client.set_refresh_handler(self.refresh_token)

    async def login(self, email: str, password: str, remember_me: bool = True) -> User:
        """Authenticates traveler with email and password."""
        payload = {"email": email.strip(), "password": password}
        data = await self.api_client.post("auth/login", json_data=payload)
        
        token_resp = AuthTokenResponse.from_dict(data)
        if not token_resp.user:
            # Fallback to fetching profile
            self.session_manager.set_authenticated_session(
                access_token=token_resp.access_token,
                refresh_token=token_resp.refresh_token,
                user=User(id="", email=email, full_name=email.split("@")[0]),
                persist=remember_me,
            )
            user = await self.get_profile()
            self.session_manager.update_user(user)
            return user

        self.session_manager.set_authenticated_session(
            access_token=token_resp.access_token,
            refresh_token=token_resp.refresh_token,
            user=token_resp.user,
            persist=remember_me,
        )
        return token_resp.user

    async def register(
        self,
        email: str,
        password: str,
        full_name: str = "",
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
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

        if not token_resp.user:
            self.session_manager.set_authenticated_session(
                access_token=token_resp.access_token,
                refresh_token=token_resp.refresh_token,
                user=User(
                    id="",
                    email=email_clean,
                    full_name=f"{first} {last}".strip(),
                    first_name=first,
                    last_name=last,
                    username=uname,
                ),
                persist=True,
            )
            user = await self.get_profile()
            self.session_manager.update_user(user)
            return user

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
                user = User(id="", email="", full_name="Traveler")

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
        """Fetches current user profile from backend."""
        data = await self.api_client.get("auth/me")
        user = User.from_dict(data)
        self.session_manager.update_user(user)
        return user

    async def update_profile(self, payload: UserUpdatePayload) -> User:
        """Updates user profile attributes."""
        data = await self.api_client.patch("auth/me", json_data=payload.to_dict())
        user = User.from_dict(data)
        self.session_manager.update_user(user)
        return user

    def continue_as_guest(self) -> None:
        """Switches session into Guest Mode."""
        self.session_manager.set_guest_mode()

    def logout(self) -> None:
        """Logs out traveler and clears tokens."""
        self.session_manager.clear_session()


_auth_service_instance: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Singleton getter for AuthService."""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService()
    return _auth_service_instance
