"""Unit tests for Place models and PlaceService."""

import pytest
from desktop_client.models.place import Municipality, PaginatedPlaces, Place
from desktop_client.services.place_service import PlaceService


def test_place_model_honest_pricing():
    # Free
    p_free = Place(
        id="1",
        name="Plaza Lucero",
        category="tourist_attraction",
        latitude=15.4865,
        longitude=120.9734,
        estimated_cost_min=0,
        estimated_cost_max=0,
    )
    assert p_free.formatted_cost == "Free Admission"

    # Exact cost
    p_exact = Place(
        id="2",
        name="Minalungao National Park",
        category="nature_park",
        latitude=15.2985,
        longitude=121.1215,
        estimated_cost_min=100.0,
        estimated_cost_max=100.0,
    )
    assert p_exact.formatted_cost == "₱100"

    # Range cost
    p_range = Place(
        id="3",
        name="Farm Heritage Resort",
        category="resort_swimming",
        latitude=15.5,
        longitude=121.0,
        estimated_cost_min=250.0,
        estimated_cost_max=500.0,
    )
    assert p_range.formatted_cost == "₱250 - ₱500"

    # Unspecified
    p_none = Place(
        id="4",
        name="Local Chapel",
        category="church_religious",
        latitude=15.5,
        longitude=121.0,
    )
    assert p_none.formatted_cost == "Estimated Cost: Free / Varies"


def test_place_category_formatting():
    p = Place(
        id="1",
        name="Cafe",
        category="hotel_accommodation",
        latitude=15.0,
        longitude=120.0,
    )
    assert p.formatted_category == "Hotel & Accommodation"


def test_municipality_model():
    m = Municipality.from_dict({
        "id": "cab-1",
        "name": "Cabanatuan City",
        "zip_code": "3100",
        "place_count": 420,
    })
    assert m.name == "Cabanatuan City"
    assert m.place_count == 420


def test_paginated_places_model():
    data = {
        "items": [
            {
                "id": "p-1",
                "name": "Pantabangan Lake",
                "category": "nature_park",
                "latitude": 15.8,
                "longitude": 121.1,
            }
        ],
        "total": 1,
        "page": 1,
        "page_size": 20,
        "total_pages": 1,
    }
    paginated = PaginatedPlaces.from_dict(data)
    assert len(paginated.items) == 1
    assert paginated.items[0].name == "Pantabangan Lake"
    assert paginated.total == 1
