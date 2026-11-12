"""Unit tests for Itinerary models and scheduling logic."""

import pytest
from desktop_client.models.itinerary import (
    Itinerary,
    ItineraryDay,
    ItineraryItem,
    SuggestedItineraryRequest,
)
from desktop_client.models.place import Place


def test_itinerary_item_display():
    place = Place(
        id="p1",
        name="Philippine Carabao Center",
        category="museum_cultural",
        latitude=15.7,
        longitude=120.9,
        estimated_cost_min=50.0,
        estimated_cost_max=50.0,
    )
    item = ItineraryItem(
        id="itm-1",
        day_id="day-1",
        place_id="p1",
        sort_order=1,
        place=place,
    )
    assert item.display_title == "Philippine Carabao Center"
    assert item.representative_cost == 50.0

    # Custom venue
    custom_item = ItineraryItem(
        id="itm-2",
        day_id="day-1",
        custom_title="Secret Farm Overlook",
        sort_order=2,
        estimated_cost_max=150.0,
    )
    assert custom_item.display_title == "Secret Farm Overlook"
    assert custom_item.representative_cost == 150.0


def test_itinerary_day_and_trip_metrics():
    item1 = ItineraryItem(
        id="1",
        day_id="d1",
        custom_title="Stop A",
        sort_order=1,
        estimated_cost_max=200.0,
    )
    item2 = ItineraryItem(
        id="2",
        day_id="d1",
        custom_title="Stop B",
        sort_order=2,
        estimated_cost_max=300.0,
    )
    day1 = ItineraryDay(
        id="d1",
        itinerary_id="itin-1",
        day_number=1,
        travel_date="2026-11-20",
        items=[item1, item2],
    )
    assert day1.total_day_cost == 500.0

    day2 = ItineraryDay(
        id="d2",
        itinerary_id="itin-1",
        day_number=2,
        travel_date="2026-11-21",
        items=[],
    )

    itin = Itinerary(
        id="itin-1",
        title="Weekend in Nueva Ecija",
        destination="Nueva Ecija",
        start_date="2026-11-20",
        end_date="2026-11-21",
        daily_budget=2500.0,
        days=[day1, day2],
    )

    assert itin.total_stops == 2
    assert itin.total_estimated_cost == 500.0
    assert len(itin.days) == 2


def test_suggested_itinerary_request():
    req = SuggestedItineraryRequest(
        title="Custom Tour",
        start_date="2026-12-01",
        end_date="2026-12-03",
        daily_budget=3000.0,
        preferences=["nature_park", "restaurant"],
        pacing="relaxed",
    )
    data = req.to_dict()
    assert data["title"] == "Custom Tour"
    assert data["daily_budget"] == 3000.0
    assert "nature_park" in data["preferences"]
    assert data["pacing"] == "relaxed"
