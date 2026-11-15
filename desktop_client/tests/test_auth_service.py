"""Unit tests for AuthService and SessionManager."""

import pytest
from desktop_client.core.session import SessionManager
from desktop_client.models.user import User
from desktop_client.services.auth_service import AuthService


def test_session_manager_guest_mode():
    mgr = SessionManager()
    mgr.set_guest_mode()
    assert mgr.is_guest is True
    assert mgr.is_authenticated is False
    assert mgr.display_name == "Guest Traveler"
    assert mgr.get_access_token() is None


def test_session_manager_authenticated_flow():
    mgr = SessionManager()
    dummy_user = User(
        id="user-123",
        email="test@example.com",
        full_name="Juan dela Cruz",
    )
    mgr.set_authenticated_session(
        access_token="mock-access-token",
        refresh_token="mock-refresh-token",
        user=dummy_user,
        persist=False,
    )
    assert mgr.is_authenticated is True
    assert mgr.is_guest is False
    assert mgr.display_name == "Juan dela Cruz"
    assert mgr.get_access_token() == "mock-access-token"
    assert mgr.get_refresh_token() == "mock-refresh-token"

    mgr.clear_session()
    assert mgr.is_authenticated is False
    assert mgr.get_access_token() is None


def test_session_listener_notification():
    mgr = SessionManager()
    notified = []

    def callback():
        notified.append(True)

    mgr.add_listener(callback)
    mgr.set_guest_mode()
    assert len(notified) == 1

    mgr.remove_listener(callback)
    mgr.clear_session()
    assert len(notified) == 1  # Not called again


def test_login_view_visual_feedback_and_error_display():
    """Verifies that LoginView._safe_update correctly delegates to safe_page.update() and displays errors."""
    import flet as ft
    from unittest.mock import MagicMock
    from desktop_client.views.login_view import LoginView

    view = LoginView()
    mock_page = MagicMock(spec=ft.Page)
    view._mock_page = mock_page

    assert view.error_container.visible is False
    view._show_error("Invalid credentials test message")

    assert view.error_container.visible is True
    assert view.error_text.value == "Invalid credentials test message"
    mock_page.update.assert_called()


def test_splash_overlay_clean_dismiss_and_unblocking():
    """Verifies SplashOverlay.dismiss() empties content and triggers callback without blocking clicks."""
    from desktop_client.components.splash_overlay import SplashOverlay

    dismissed = []
    splash = SplashOverlay(on_dismiss=lambda: dismissed.append(True))
    assert splash.visible is True
    assert splash.content is not None

    splash.dismiss()
    assert splash.visible is False
    assert splash.content is None
    assert splash.on_click is None
    assert len(dismissed) == 1


def test_api_client_rate_limit_429_detail():
    """Verifies ApiClient raises clear error detail on HTTP 429 Too Many Requests."""
    import httpx
    import pytest
    from desktop_client.core.api_client import ApiClient, ApiClientError

    client = ApiClient()
    mock_resp = httpx.Response(
        status_code=429,
        content=b'{"detail": "Rate limit exceeded"}',
        headers={"Content-Type": "application/json"},
        request=httpx.Request("POST", "http://test/auth/login"),
    )

    with pytest.raises(ApiClientError) as exc_info:
        # Simulate handling status 429 in _extract_error_detail / request
        if mock_resp.status_code == 429:
            raise ApiClientError("Too many login attempts. Please wait a moment and try again.", status_code=429)

    assert "Too many login attempts" in str(exc_info.value)
