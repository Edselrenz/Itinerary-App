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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str = "traveler"
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        first_name = str(data.get("first_name", "")).strip()
        last_name = str(data.get("last_name", "")).strip()
        username = str(data.get("username") or data.get("username_normalized") or "").strip()
        email = str(data.get("email") or data.get("email_normalized") or "").strip()
        
        full_name = str(data.get("full_name", "")).strip()
        if not full_name:
            if first_name or last_name:
                full_name = f"{first_name} {last_name}".strip()
            elif username:
                full_name = username
            elif email:
                full_name = email.split("@")[0]
            else:
                full_name = "Traveler"

        return cls(
            id=str(data.get("id", "")),
            email=email,
            full_name=full_name,
            first_name=first_name or None,
            last_name=last_name or None,
            username=username or None,
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
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
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
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {}
        if self.first_name:
            res["first_name"] = self.first_name
        elif self.full_name:
            parts = self.full_name.strip().split(maxsplit=1)
            res["first_name"] = parts[0]
            if len(parts) > 1:
                res["last_name"] = parts[1]

        if self.last_name is not None and "last_name" not in res:
            res["last_name"] = self.last_name
        if self.username is not None:
            res["username"] = self.username
        if self.avatar_url is not None:
            res["avatar_url"] = self.avatar_url
        if self.current_password:
            res["current_password"] = self.current_password
        if self.new_password:
            res["new_password"] = self.new_password
        return res
