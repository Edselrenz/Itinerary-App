"""Local persistence for Guest Mode and Offline Itineraries."""

import json
from pathlib import Path
from typing import Any, Optional
import uuid

from desktop_client.config.settings import get_settings
from desktop_client.models.itinerary import Itinerary, ItineraryDay, ItineraryItem


class GuestStorageManager:
    """Manages locally persisted itineraries when unauthenticated or working offline.

    Directly mirrors the web client's 'ne_guest_itineraries_v1' storage behavior,
    ensuring guest travelers never lose custom or generated travel plans.
    """

    def __init__(self):
        settings = get_settings()
        self.storage_file = settings.storage_dir / "guest_storage.json"
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.storage_file.exists():
            try:
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    json.dump({"itineraries": []}, f, indent=2)
            except Exception:
                pass

    def _read_data(self) -> list[dict[str, Any]]:
        try:
            if not self.storage_file.exists():
                return []
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("itineraries", [])
        except Exception:
            return []

    def _write_data(self, itineraries: list[dict[str, Any]]) -> None:
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump({"itineraries": itineraries}, f, indent=2)
        except Exception:
            pass

    def list_itineraries(self) -> list[Itinerary]:
        """Lists all guest itineraries stored on the local desktop."""
        raw_list = self._read_data()
        results: list[Itinerary] = []
        for item in raw_list:
            try:
                itin = Itinerary.from_dict(item)
                itin.is_guest = True
                results.append(itin)
            except Exception:
                continue
        return results

    def get_itinerary(self, itinerary_id: str) -> Optional[Itinerary]:
        """Retrieves a single guest itinerary by UUID."""
        raw_list = self._read_data()
        for item in raw_list:
            if item.get("id") == itinerary_id:
                itin = Itinerary.from_dict(item)
                itin.is_guest = True
                return itin
        return None

    def save_itinerary(self, itinerary: Itinerary) -> Itinerary:
        """Saves or updates an itinerary in local guest storage."""
        itinerary.is_guest = True
        raw_list = self._read_data()
        
        # Check if already present
        existing_index = next(
            (idx for idx, item in enumerate(raw_list) if item.get("id") == itinerary.id),
            None,
        )
        
        itin_dict = itinerary.to_dict()
        if existing_index is not None:
            raw_list[existing_index] = itin_dict
        else:
            raw_list.insert(0, itin_dict)

        self._write_data(raw_list)
        return itinerary

    def delete_itinerary(self, itinerary_id: str) -> bool:
        """Deletes a guest itinerary by ID."""
        raw_list = self._read_data()
        new_list = [item for item in raw_list if item.get("id") != itinerary_id]
        if len(new_list) != len(raw_list):
            self._write_data(new_list)
            return True
        return False

    def clear_all(self) -> None:
        """Clears all stored guest itineraries."""
        self._write_data([])


_guest_storage_instance: Optional[GuestStorageManager] = None


def get_guest_storage() -> GuestStorageManager:
    """Singleton getter for GuestStorageManager."""
    global _guest_storage_instance
    if _guest_storage_instance is None:
        _guest_storage_instance = GuestStorageManager()
    return _guest_storage_instance
