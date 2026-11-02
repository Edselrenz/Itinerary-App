"""Unit & API integration tests for Traveler Authentication, Argon2id, and JWT."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
for d in [str(BACKEND_DIR), str(ROOT_DIR)]:
    if d not in sys.path:
        sys.path.insert(0, d)

from app.core.database import Base, get_db
from app.main import app


def make_test_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_auth_lifecycle():
    TestingSessionLocal = make_test_session()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # 1. Register a new traveler
    reg_payload = {
        "first_name": "Juan",
        "last_name": "Dela Cruz",
        "username": "juandelacruz",
        "email": "juan.delacruz@example.ph",
        "password": "Password123!",
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username_normalized"] == "juandelacruz"
    assert data["user"]["email_normalized"] == "juan.delacruz@example.ph"
    token = data["access_token"]
    refresh_token = data["refresh_token"]

    # 2. Reject duplicate username (case-insensitive)
    dup_user_payload = {
        "first_name": "Another",
        "last_name": "User",
        "username": "JUANdelaCruz",  # different case
        "email": "another@example.ph",
        "password": "Password123!",
    }
    dup_res = client.post("/api/v1/auth/register", json=dup_user_payload)
    assert dup_res.status_code == 409
    assert "Username" in dup_res.json()["detail"]

    # 3. Reject duplicate email (case-insensitive)
    dup_email_payload = {
        "first_name": "Another",
        "last_name": "User",
        "username": "anotheruser",
        "email": "JUAN.DELACRUZ@example.ph",  # uppercase
        "password": "Password123!",
    }
    dup_email_res = client.post("/api/v1/auth/register", json=dup_email_payload)
    assert dup_email_res.status_code == 409
    assert "Email" in dup_email_res.json()["detail"]

    # 4. Failed login: wrong password
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": "juan.delacruz@example.ph", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401
    assert "Invalid email or password" in bad_login.json()["detail"]

    # 5. Successful login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "JUAN.delacruz@example.ph", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    access_token = login_data["access_token"]

    # 6. Fetch /auth/me with Bearer token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["first_name"] == "Juan"
    assert me_res.json()["last_name"] == "Dela Cruz"

    # 7. Unauthenticated /auth/me
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401

    # 8. Refresh token exchange
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()

    # 9. Apple Sign-In returns 501 truthful error
    apple_res = client.post("/api/v1/auth/oauth/apple")
    assert apple_res.status_code == 501
    assert "Apple Sign-In is disabled" in apple_res.json()["detail"]


def test_auth_rate_limiting():
    """Verifies that SlowAPI throttles rapid authentication attempts after 5 requests/minute."""
    from app.core.limiter import limiter

    limiter.reset()
    client = TestClient(app)

    responses = []
    for i in range(6):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": f"attacker_{i}@example.ph", "password": "InvalidPassword123!"},
        )
        responses.append(res)

    # First 5 attempts return 401 (credentials check)
    for res in responses[:5]:
        assert res.status_code == 401

    # 6th attempt is throttled with 429 Too Many Requests
    assert responses[5].status_code == 429
    assert "Rate limit exceeded" in responses[5].text


def test_cloudflare_tunnel_ip_resolution():
    """CR-013: Verifies get_client_ip extracts CF-Connecting-IP and X-Forwarded-For behind tunnels."""
    from starlette.datastructures import Address, Headers
    from starlette.requests import Request
    from app.core.limiter import get_client_ip

    def make_mock_request(client_ip: str | None, headers: dict[str, str]) -> Request:
        scope = {
            "type": "http",
            "client": Address(client_ip, 12345) if client_ip else None,
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        }
        return Request(scope)

    # 1. Cloudflare Tunnel with CF-Connecting-IP
    req_cf = make_mock_request("127.0.0.1", {"CF-Connecting-IP": "203.0.113.42"})
    assert get_client_ip(req_cf) == "203.0.113.42"

    # 2. Localhost reverse proxy with X-Forwarded-For chain
    req_xff = make_mock_request("localhost", {"X-Forwarded-For": "198.51.100.9, 10.0.0.1"})
    assert get_client_ip(req_xff) == "198.51.100.9"

    # 3. Direct external client cannot spoof CF-Connecting-IP
    req_direct = make_mock_request("192.0.2.1", {"CF-Connecting-IP": "203.0.113.99"})
    assert get_client_ip(req_direct) == "192.0.2.1"

    # 4. Fallback when no client address is provided
    req_none = make_mock_request(None, {})
    assert get_client_ip(req_none) == "127.0.0.1"


def test_auth_rate_limiting_isolated_by_cloudflare_ip():
    """CR-013: Verifies distinct Cloudflare IPs have isolated rate limit buckets behind tunnel."""
    from app.core.limiter import limiter

    limiter.reset()
    client = TestClient(app)

    # 5 attempts from User A behind Cloudflare
    for i in range(5):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": f"usera_{i}@example.ph", "password": "WrongPassword!"},
            headers={"CF-Connecting-IP": "203.0.113.100"},
        )
        assert res.status_code == 401

    # 6th attempt from User A is throttled (429)
    res_a_blocked = client.post(
        "/api/v1/auth/login",
        json={"email": "usera_blocked@example.ph", "password": "WrongPassword!"},
        headers={"CF-Connecting-IP": "203.0.113.100"},
    )
    assert res_a_blocked.status_code == 429

    # First attempt from User B with different CF-Connecting-IP must succeed (401 credentials check, not 429)
    res_b = client.post(
        "/api/v1/auth/login",
        json={"email": "userb@example.ph", "password": "WrongPassword!"},
        headers={"CF-Connecting-IP": "203.0.113.200"},
    )
    assert res_b.status_code == 401



def test_settings_secret_validation_in_production():
    """CR-004: Verifies Settings rejects default JWT secret key outside development."""
    import pytest
    from app.core.config import Settings

    with pytest.raises(ValueError, match="jwt_secret_key must be explicitly configured"):
        Settings(
            app_env="production",
            jwt_secret_key="dev_only_replace_before_pilot_with_openssl_rand_hex_32",
        )


def test_google_oauth_security_hardening():
    """CR-004 & CR-005: Verifies unconfigured client ID, unverified emails, and deactivated accounts."""
    from unittest.mock import patch
    from fastapi import HTTPException
    from app.models.entities import User
    from app.services.auth_service import authenticate_google_user, verify_google_id_token
    from app.core.config import settings

    TestingSessionLocal = make_test_session()
    db = TestingSessionLocal()

    # 1. CR-004: Unconfigured google_oauth_client_id raises 503
    with patch.object(settings, "google_oauth_client_id", ""):
        try:
            verify_google_id_token("dummy-token")
            assert False, "Should have raised HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 503
            assert "client ID is not configured" in exc.detail

    # 2. CR-005: Unverified Google email rejected with 400 Bad Request
    with patch("app.services.auth_service.verify_google_id_token") as mock_verify:
        mock_verify.return_value = {
            "sub": "google-123",
            "email": "unverified@example.ph",
            "email_verified": False,
        }
        try:
            authenticate_google_user(db, "unverified-token")
            assert False, "Should have raised HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 400
            assert "not verified" in exc.detail

    # 3. CR-005: Deactivated existing user rejected with 403 Forbidden
    inactive_user = User(
        first_name="Banned",
        last_name="User",
        username_normalized="banneduser",
        email_normalized="banned@example.ph",
        password_hash=None,
        is_active=False,
    )
    db.add(inactive_user)
    db.commit()

    with patch("app.services.auth_service.verify_google_id_token") as mock_verify:
        mock_verify.return_value = {
            "sub": "google-456",
            "email": "banned@example.ph",
            "email_verified": True,
        }
        try:
            authenticate_google_user(db, "banned-token")
            assert False, "Should have raised HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 403
            assert "deactivated" in exc.detail

    db.close()



