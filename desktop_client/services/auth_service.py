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

    async def register(self, email: str, password: str, full_name: str) -> User:
        """Registers a new traveler account with Argon2id hash."""
        payload = {
            "email": email.strip(),
            "password": password,
            "full_name": full_name.strip(),
        }
        data = await self.api_client.post("auth/register", json_data=payload)
        token_resp = AuthTokenResponse.from_dict(data)

        if not token_resp.user:
            self.session_manager.set_authenticated_session(
                access_token=token_resp.access_token,
                refresh_token=token_resp.refresh_token,
                user=User(id="", email=email, full_name=full_name),
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
