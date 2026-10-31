"""Authentication service implementing Argon2id hashing, JWT, and Google OAuth."""

import uuid
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import jwt
from pwdlib import PasswordHash
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import AuthIdentity, User
from app.schemas.auth import UserRegisterIn

password_hasher = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
    auto_error=False,
)


def normalize_identifier(value: str) -> str:
    """Normalizes emails and usernames to lowercase without surrounding whitespace."""
    return value.strip().lower()


def hash_password(plain_password: str) -> str:
    """Hashes a password using Argon2id."""
    return password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verifies a plain password against an Argon2id hash."""
    if not hashed_password:
        return False
    return password_hasher.verify(plain_password, hashed_password)


def create_jwt_token(payload: dict, expires_delta: timedelta) -> str:
    """Creates a signed JWT with standard claims."""
    now = datetime.now(timezone.utc)
    to_encode = payload.copy()
    to_encode.update({"iat": now, "exp": now + expires_delta})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: uuid.UUID) -> str:
    """Issues a short-lived access token (default 30 minutes)."""
    return create_jwt_token(
        {"sub": str(user_id), "type": "access"},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Issues a long-lived refresh token (default 7 days)."""
    return create_jwt_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_jwt_token(token: str, expected_type: str = "access") -> dict:
    """Validates and decodes a signed JWT."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type: expected {expected_type}",
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def register_user(db: Session, data: UserRegisterIn) -> User:
    """Registers a new traveler account with uniqueness enforcement."""
    norm_email = normalize_identifier(data.email)
    norm_username = normalize_identifier(data.username)

    existing = db.scalar(
        select(User).where(
            or_(
                User.email_normalized == norm_email,
                User.username_normalized == norm_username,
            )
        )
    )
    if existing:
        if existing.email_normalized == norm_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken",
        )

    user = User(
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        username_normalized=norm_username,
        email_normalized=norm_email,
        password_hash=hash_password(data.password),
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or username already exists",
        )
    return user


def authenticate_user(db: Session, identifier: str, password: str) -> User:
    """Authenticates email/username with Argon2id; uses generic 401 to prevent enumeration."""
    norm_id = normalize_identifier(identifier)
    user = db.scalar(
        select(User).where(
            or_(
                User.email_normalized == norm_id,
                User.username_normalized == norm_id,
            )
        )
    )
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    return user


def verify_google_id_token(raw_id_token: str) -> dict:
    """Server-side verification of Google OAuth ID token."""
    try:
        idinfo = id_token.verify_oauth2_token(
            raw_id_token,
            google_requests.Request(),
            settings.google_oauth_client_id or None,
        )
        if idinfo.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
            raise ValueError("Invalid Google token issuer")
        return idinfo
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google token verification failed: {exc}",
        )


def authenticate_google_user(db: Session, raw_id_token: str) -> User:
    """Links or provisions an account via Google OAuth ID token sub identifier."""
    info = verify_google_id_token(raw_id_token)
    provider_sub = str(info["sub"])
    provider_email = info.get("email")

    identity = db.scalar(
        select(AuthIdentity).where(
            AuthIdentity.provider == "google",
            AuthIdentity.provider_subject == provider_sub,
        )
    )

    if identity:
        return identity.user

    # If identity not found, check if a user with same email exists
    norm_email = normalize_identifier(provider_email) if provider_email else None
    user = None
    if norm_email:
        user = db.scalar(select(User).where(User.email_normalized == norm_email))

    if not user:
        # Create new user for this Google account
        given_name = info.get("given_name") or "Traveler"
        family_name = info.get("family_name") or "User"
        base_username = (norm_email.split("@")[0] if norm_email else "user")[:35]
        candidate_username = base_username
        suffix = 1
        while db.scalar(select(User).where(User.username_normalized == candidate_username)):
            candidate_username = f"{base_username}_{suffix}"
            suffix += 1

        user = User(
            first_name=given_name,
            last_name=family_name,
            username_normalized=candidate_username,
            email_normalized=norm_email or f"{provider_sub}@google.local",
            password_hash=None,
            is_active=True,
        )
        db.add(user)
        db.flush()

    new_identity = AuthIdentity(
        user_id=user.id,
        provider="google",
        provider_subject=provider_sub,
        provider_email=provider_email,
    )
    db.add(new_identity)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependency for extracting and validating the authenticated user from the Bearer token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_jwt_token(token, expected_type="access")
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user identifier",
        )

    user = db.scalar(select(User).where(User.id == user_uuid))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Dependency for extracting the authenticated user if a valid Bearer token is provided, or None."""
    if not token:
        return None
    try:
        payload = decode_jwt_token(token, expected_type="access")
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user_uuid = uuid.UUID(user_id_str)
        user = db.scalar(select(User).where(User.id == user_uuid))
        if user and user.is_active:
            return user
    except Exception:
        return None
    return None


