"""REST endpoints for Traveler Authentication, Registration, and OAuth."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import User
from app.schemas.auth import (
    GoogleOAuthIn,
    RefreshTokenIn,
    TokenOut,
    UserLoginIn,
    UserOut,
    UserRegisterIn,
)
from app.services.auth_service import (
    authenticate_google_user,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    get_current_user,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def make_token_response(user: User) -> TokenOut:
    """Helper to generate access/refresh tokens and serialized user."""
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return TokenOut(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegisterIn,
    db: Session = Depends(get_db),
) -> TokenOut:
    """Registers a new account with Argon2id password hash and returns JWT session."""
    user = register_user(db, payload)
    return make_token_response(user)


@router.post("/login", response_model=TokenOut)
def login(
    payload: UserLoginIn,
    db: Session = Depends(get_db),
) -> TokenOut:
    """Validates user credentials and issues access + refresh JWTs."""
    user = authenticate_user(db, payload.email, payload.password)
    return make_token_response(user)


@router.post("/refresh", response_model=TokenOut)
def refresh_session(
    payload: RefreshTokenIn,
    db: Session = Depends(get_db),
) -> TokenOut:
    """Exchanges a valid refresh token for a fresh token pair."""
    decoded = decode_jwt_token(payload.refresh_token, expected_type="refresh")
    user_id_str = decoded.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token identifier",
        )
    user = db.scalar(select(User).where(User.id == user_uuid))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return make_token_response(user)


@router.get("/me", response_model=UserOut)
def get_profile(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """Returns the authenticated traveler profile."""
    return UserOut.model_validate(current_user)


@router.post("/oauth/google", response_model=TokenOut)
def google_oauth(
    payload: GoogleOAuthIn,
    db: Session = Depends(get_db),
) -> TokenOut:
    """Validates Google ID token server-side and provisions or links user account."""
    user = authenticate_google_user(db, payload.id_token)
    return make_token_response(user)


@router.post("/oauth/apple", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def apple_oauth() -> None:
    """Truthful gate for Apple Sign-In; requires US$99/yr Apple Developer Program membership."""
    if not settings.enable_apple_auth:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Apple Sign-In is disabled in this pilot build until Apple Developer Program membership is configured.",
        )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Apple Sign-In credentials pending configuration.",
    )
