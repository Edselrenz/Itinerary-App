"""Persistent traveler favorites service backed by storage/favorites.json.

Mirrors Project/src/app/core/services/favorites.service.ts for Desktop Parity.
"""

import json
from pathlib import Path
from typing import Callable, Optional

from desktop_client.config.settings import get_settings
from desktop_client.core.offline_data import CANONICAL_OFFLINE_PLACES
from desktop_client.models.place import Place


class FavoritesService:
    """Manages saved traveler favorites with local JSON persistence."""

    def __init__(self):
        self.settings = get_settings()
        self.favorites_file = self.settings.storage_dir / "favorites.json"
        self._favorites: list[Place] = []
        self._listeners: list[Callable[[], None]] = []
        self._load()

    def add_listener(self, callback: Callable[[], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self) -> None:
        for cb in self._listeners:
            try:
                cb()
            except Exception:
                pass

    def _load(self) -> None:
        if not self.favorites_file.exists():
            self._seed_default_favorites()
            return

        try:
            with open(self.favorites_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    self._favorites = [Place.from_dict(item) for item in data]
                else:
                    self._seed_default_favorites()
        except Exception:
            self._seed_default_favorites()

    def _seed_default_favorites(self) -> None:
        """Seeds initial 3 iconic Nueva Ecija places on first launch."""
        seeded = []
        target_ids = {"dest-rohi-paperflower", "dest-museo-bongabon", "dest-minalungao"}
        for cp in CANONICAL_OFFLINE_PLACES:
            if cp.id in target_ids:
                seeded.append(Place.from_dict(cp.to_dict()))

        self._favorites = seeded
        self._save()

    def _save(self) -> None:
        try:
            data = [p.to_dict() for p in self._favorites]
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
        self._notify()

    def get_favorites(self) -> list[Place]:
        return list(self._favorites)

    def is_favorite(self, place_id: str) -> bool:
        if not place_id:
            return False
        clean_id = str(place_id).strip()
        return any(p.id == clean_id for p in self._favorites)

    def add_favorite(self, place: Place) -> bool:
        if self.is_favorite(place.id):
            return False
        self._favorites.insert(0, place)
        self._save()
        return True

    def remove_favorite(self, place_id: str) -> bool:
        clean_id = str(place_id).strip()
        orig_len = len(self._favorites)
        self._favorites = [p for p in self._favorites if p.id != clean_id]
        if len(self._favorites) != orig_len:
            self._save()
            return True
        return False

    def toggle_favorite(self, place: Place) -> bool:
        """Toggles favorite state. Returns True if now favored, False if removed."""
        if self.is_favorite(place.id):
            self.remove_favorite(place.id)
            return False
        else:
            self.add_favorite(place)
            return True


_favorites_service_instance: Optional[FavoritesService] = None


def get_favorites_service() -> FavoritesService:
    global _favorites_service_instance
    if _favorites_service_instance is None:
        _favorites_service_instance = FavoritesService()
    return _favorites_service_instance
