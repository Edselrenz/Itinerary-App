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
