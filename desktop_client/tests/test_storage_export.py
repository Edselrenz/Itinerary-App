"""Unit tests for GuestStorageManager and Export formatting."""

import json
from pathlib import Path
import pytest
from desktop_client.core.export import export_to_ics, export_to_json, export_to_text
from desktop_client.core.storage import GuestStorageManager
from desktop_client.models.itinerary import Itinerary, ItineraryDay, ItineraryItem
from desktop_client.models.place import Place


@pytest.fixture
def sample_itinerary():
    place = Place(
        id="p-minalungao",
        name="Minalungao National Park",
        category="nature_park",
        latitude=15.2985,
        longitude=121.1215,
        municipality_name="General Tinio",
        address_text="General Tinio, Nueva Ecija",
        estimated_cost_min=100.0,
        estimated_cost_max=100.0,
    )
    stop1 = ItineraryItem(
        id="stop-1",
        day_id="day-1",
        place_id=place.id,
        sort_order=1,
        planned_time="09:00",
        duration_minutes=120,
        notes="Bring swimwear and cash for bamboo raft rental",
        place=place,
    )
    stop2 = ItineraryItem(
        id="stop-2",
        day_id="day-1",
        custom_title="Riverside Picnic Spot",
        sort_order=2,
        planned_time="12:00",
        duration_minutes=60,
        estimated_cost_max=200.0,
    )
    day1 = ItineraryDay(
        id="day-1",
        itinerary_id="itin-test",
        day_number=1,
        travel_date="2026-11-25",
        title="Nature & River Adventure",
        items=[stop1, stop2],
    )
    return Itinerary(
        id="itin-test",
        title="Nueva Ecija Adventure",
        destination="Nueva Ecija",
        start_date="2026-11-25",
        end_date="2026-11-25",
        daily_budget=2000.0,
        days=[day1],
    )


def test_export_to_ics(sample_itinerary):
    ics_text = export_to_ics(sample_itinerary)
    assert "BEGIN:VCALENDAR" in ics_text
    assert "END:VCALENDAR" in ics_text
    assert "BEGIN:VEVENT" in ics_text
    assert "Minalungao National Park" in ics_text
    assert "Riverside Picnic Spot" in ics_text
    assert "DTSTART:" in ics_text
    assert "DTEND:" in ics_text


def test_export_to_text(sample_itinerary):
    txt = export_to_text(sample_itinerary)
    assert "# Nueva Ecija Adventure" in txt
    assert "Minalungao National Park" in txt
    assert "Riverside Picnic Spot" in txt
    assert "Total Estimated Cost:" in txt
    assert "General Tinio" in txt


def test_export_to_json(sample_itinerary):
    json_str = export_to_json(sample_itinerary)
    data = json.loads(json_str)
    assert data["title"] == "Nueva Ecija Adventure"
    assert len(data["days"]) == 1
    assert len(data["days"][0]["items"]) == 2


def test_guest_storage_crud(sample_itinerary, tmp_path):
    storage = GuestStorageManager()
    storage.storage_file = tmp_path / "test_guest_storage.json"
    storage._ensure_file()

    # Save
    saved = storage.save_itinerary(sample_itinerary)
    assert saved.id == sample_itinerary.id

    # List
    items = storage.list_itineraries()
    assert len(items) == 1
    assert items[0].id == sample_itinerary.id
    assert items[0].is_guest is True

    # Get
    retrieved = storage.get_itinerary(sample_itinerary.id)
    assert retrieved is not None
    assert retrieved.title == sample_itinerary.title

    # Delete
    deleted = storage.delete_itinerary(sample_itinerary.id)
    assert deleted is True
    assert len(storage.list_itineraries()) == 0
