"""User and Authentication data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class User:
    """Traveler account profile."""
    
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    role: str = "traveler"
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        return cls(
            id=str(data.get("id", "")),
            email=str(data.get("email", "")),
            full_name=str(data.get("full_name", "")),
            avatar_url=data.get("avatar_url"),
            role=str(data.get("role", "traveler")),
            is_active=bool(data.get("is_active", True)),
            is_verified=bool(data.get("is_verified", False)),
            created_at=str(data.get("created_at")) if data.get("created_at") else None,
            updated_at=str(data.get("updated_at")) if data.get("updated_at") else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class AuthTokenResponse:
    """JWT response payload containing access and refresh tokens."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[User] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthTokenResponse":
        user_obj = None
        if "user" in data and isinstance(data["user"], dict):
            user_obj = User.from_dict(data["user"])
        return cls(
            access_token=str(data.get("access_token", "")),
            refresh_token=str(data.get("refresh_token", "")),
            token_type=str(data.get("token_type", "bearer")),
            user=user_obj,
        )


@dataclass
class UserUpdatePayload:
    """Payload to update traveler profile."""
    
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {}
        if self.full_name is not None:
            res["full_name"] = self.full_name
        if self.avatar_url is not None:
            res["avatar_url"] = self.avatar_url
        return res
