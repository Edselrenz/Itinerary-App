"""Live integration test against running FastAPI backend."""

import asyncio
from datetime import date, timedelta
import pytest

from desktop_client.core.api_client import get_api_client
from desktop_client.core.export import export_to_ics, export_to_text, export_to_json
from desktop_client.models.itinerary import SuggestedItineraryRequest
from desktop_client.services.itinerary_service import get_itinerary_service
from desktop_client.services.place_service import get_place_service


def test_live_backend_integration():
    api = get_api_client()
    if not api.check_health_sync():
        pytest.skip("FastAPI backend is not running on port 8000")

    async def _runner():
        place_svc = get_place_service()
        munis = await place_svc.get_municipalities()
        assert len(munis) >= 10
        assert any(m.name == "Cabanatuan City" for m in munis)

        # Places query
        places = await place_svc.get_places(page=1, page_size=5, category="nature_park")
        assert len(places.items) > 0
        assert places.total > 0

        # Suggested Itinerary generation
        today = date.today()
        itin_svc = get_itinerary_service()
        req = SuggestedItineraryRequest(
            title="Automated Test Trip",
            destination="Nueva Ecija",
            start_date=(today + timedelta(days=10)).strftime("%Y-%m-%d"),
            end_date=(today + timedelta(days=12)).strftime("%Y-%m-%d"),
            daily_budget=2500.0,
            preferences=["nature_park", "restaurant"],
            pacing="moderate",
            save_immediately=False,
        )
        suggested = await itin_svc.generate_suggested_itinerary(req)
        assert suggested is not None
        assert len(suggested.days) == 3
        assert suggested.total_stops > 0

        # Export formats
        ics_data = export_to_ics(suggested)
        assert "BEGIN:VCALENDAR" in ics_data
        assert "DTSTART:" in ics_data

        txt_data = export_to_text(suggested)
        assert "Automated Test Trip" in txt_data
        assert "Nueva Ecija" in txt_data

        json_data = export_to_json(suggested)
        assert "Automated Test Trip" in json_data

    asyncio.run(_runner())
