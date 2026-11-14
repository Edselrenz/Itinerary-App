"""User and authentication domain models aligned 1:1 with backend/app/schemas/user.py and Web App."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class User:
    """Represents an authenticated or guest user with backend + local extended profile fields."""

    id: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    middle_initial: str = ""
    username: str = ""
    full_name: Optional[str] = None
    birthday: str = ""
    gender: str = ""
    phone_number: str = ""
    avatar_url: Optional[str] = None
    role: str = "traveler"
    is_active: bool = True
    is_guest: bool = False
    is_verified: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    preferences: list[str] = field(default_factory=list)
    default_daily_budget: float = 3000.0

    def __post_init__(self) -> None:
        if self.full_name and not self.first_name and not self.last_name:
            parts = self.full_name.strip().split(" ", 1)
            self.first_name = parts[0]
            if len(parts) > 1:
                self.last_name = parts[1]

        # Ensure full_name is populated
        self.full_name = self._compute_full_name()

    def _compute_full_name(self) -> str:
        """Construct display name from first_name, middle_initial, and last_name."""
        parts: list[str] = []
        if self.first_name and self.first_name.strip():
            parts.append(self.first_name.strip())
        if self.middle_initial and self.middle_initial.strip():
            mi = self.middle_initial.strip().rstrip(".")
            parts.append(f"{mi}.")
        if self.last_name and self.last_name.strip():
            parts.append(self.last_name.strip())
        joined = " ".join(parts).strip()
        if joined:
            return joined
        if self.username and self.username.strip():
            return self.username.strip()
        if self.email and self.email.strip():
            return self.email.split("@")[0]
        return "Guest Explorer" if self.is_guest else "Traveler"


    @classmethod
    def from_dict(cls, data: dict[str, Any], extra: Optional[dict[str, Any]] = None) -> "User":
        extra = extra or {}
        raw_first = str(data.get("first_name") or extra.get("first_name") or "").strip()
        raw_last = str(data.get("last_name") or extra.get("last_name") or "").strip()

        # Fallback if legacy data only stored full_name
        if not raw_first and not raw_last and data.get("full_name"):
            tokens = str(data.get("full_name")).strip().split(" ", 1)
            raw_first = tokens[0]
            raw_last = tokens[1] if len(tokens) > 1 else ""

        email_val = str(
            data.get("email_normalized")
            or data.get("email")
            or extra.get("email")
            or ""
        ).strip()
        username_val = str(
            data.get("username_normalized")
            or data.get("username")
            or extra.get("username")
            or (email_val.split("@")[0] if email_val else "")
        ).strip()

        prefs = extra.get("preferences", data.get("preferences", []))
        if isinstance(prefs, str):
            prefs = [p.strip() for p in prefs.split(",") if p.strip()]

        return cls(
            id=str(data.get("id", "guest-local")),
            first_name=raw_first,
            last_name=raw_last,
            middle_initial=str(extra.get("middle_initial") or data.get("middle_initial") or "").strip(),
            username=username_val,
            email=email_val,
            birthday=str(extra.get("birthday") or data.get("birthday") or "").strip(),
            gender=str(extra.get("gender") or data.get("gender") or "").strip(),
            phone_number=str(extra.get("phone_number") or data.get("phone_number") or "").strip(),
            avatar_url=extra.get("avatar_url") or data.get("avatar_url"),
            role=str(data.get("role", "traveler")),
            is_active=bool(data.get("is_active", True)),
            is_guest=bool(data.get("is_guest", False)),
            is_verified=bool(data.get("is_verified", False)),
            created_at=str(data.get("created_at")) if data.get("created_at") else None,
            updated_at=str(data.get("updated_at")) if data.get("updated_at") else None,
            preferences=list(prefs) if isinstance(prefs, list) else [],
            default_daily_budget=float(
                extra.get("default_daily_budget", data.get("default_daily_budget", 3000.0)) or 3000.0
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_initial": self.middle_initial,
            "username": self.username,
            "username_normalized": self.username,
            "email": self.email,
            "email_normalized": self.email,
            "full_name": self.full_name,
            "birthday": self.birthday,
            "gender": self.gender,
            "phone_number": self.phone_number,
            "avatar_url": self.avatar_url,
            "role": self.role,
            "is_active": self.is_active,
            "is_guest": self.is_guest,
            "is_verified": self.is_verified,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "preferences": self.preferences,
            "default_daily_budget": self.default_daily_budget,
        }

    @classmethod
    def create_guest(cls, extra: Optional[dict[str, Any]] = None) -> "User":
        extra = extra or {}
        return cls(
            id="guest-local",
            first_name=str(extra.get("first_name") or "Guest"),
            last_name=str(extra.get("last_name") or "Explorer"),
            middle_initial=str(extra.get("middle_initial") or ""),
            username=str(extra.get("username") or "guest_explorer"),
            email=str(extra.get("email") or "guest@local.offline"),
            birthday=str(extra.get("birthday") or ""),
            gender=str(extra.get("gender") or ""),
            phone_number=str(extra.get("phone_number") or ""),
            avatar_url=extra.get("avatar_url"),
            role="guest",
            is_active=True,
            is_guest=True,
            is_verified=False,
            preferences=list(extra.get("preferences", ["Nature & Parks", "Food Trip", "Culture & History"])),
            default_daily_budget=float(extra.get("default_daily_budget", 2500.0)),
        )


@dataclass
class AuthTokens:
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthTokens":
        return cls(
            access_token=str(data.get("access_token", "")),
            refresh_token=data.get("refresh_token"),
            token_type=str(data.get("token_type", "bearer")),
        )


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
    """Payload for updating profile across FastAPI PATCH /api/v1/auth/me + LocalStorage extended metadata."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    birthday: Optional[str] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[list[str]] = None
    default_daily_budget: Optional[float] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

    def to_backend_dict(self) -> dict[str, Any]:
        """Exact fields accepted by FastAPI UserUpdateIn (backend/app/schemas/user.py)."""
        payload: dict[str, Any] = {}
        first = self.first_name
        last = self.last_name
        if not first and self.full_name:
            tokens = self.full_name.strip().split(" ", 1)
            first = tokens[0]
            if len(tokens) > 1 and not last:
                last = tokens[1]

        if first is not None and len(first.strip()) >= 1:
            payload["first_name"] = first.strip()
        if last is not None and len(last.strip()) >= 1:
            payload["last_name"] = last.strip()
        if self.username is not None and len(self.username.strip()) >= 3:
            payload["username"] = self.username.strip()
        if self.current_password and self.new_password:
            payload["current_password"] = self.current_password
            payload["new_password"] = self.new_password
        return payload

    def to_extra_dict(self) -> dict[str, Any]:
        """Extended profile fields persisted locally in profile_extra_{user_id}."""
        extra: dict[str, Any] = {}
        for key in (
            "first_name",
            "last_name",
            "middle_initial",
            "username",
            "email",
            "birthday",
            "gender",
            "phone_number",
            "avatar_url",
            "preferences",
            "default_daily_budget",
        ):
            val = getattr(self, key, None)
            if val is not None:
                extra[key] = val
        return extra

    def to_dict(self) -> dict[str, Any]:
        """Backwards compatibility for methods expecting to_dict()."""
        return self.to_backend_dict()
