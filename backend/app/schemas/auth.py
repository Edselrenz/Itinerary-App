"""Pydantic v2 schemas for Authentication, Registration, and Tokens."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterIn(BaseModel):
    """User registration request payload."""

    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLoginIn(BaseModel):
    """User login request payload."""

    email: str = Field(..., description="Email address or username")
    password: str = Field(..., min_length=1)


class RefreshTokenIn(BaseModel):
    """JWT refresh token payload."""

    refresh_token: str


class GoogleOAuthIn(BaseModel):
    """Google OAuth ID token verification payload."""

    id_token: str


class UserOut(BaseModel):
    """Public user profile serializer."""

    id: uuid.UUID
    first_name: str
    last_name: str
    username_normalized: str
    email_normalized: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    """Signed JWT tokens and user profile."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut

