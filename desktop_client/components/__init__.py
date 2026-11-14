"""UI Components for Nueva Ecija Travel Desktop Client."""

from desktop_client.components.bottom_tab_bar import BottomTabBar
from desktop_client.components.offline_banner import OfflineHostBanner
from desktop_client.components.splash_overlay import SplashOverlay
from desktop_client.components.workflow_header import WorkflowHeader
from desktop_client.components.itinerary_route_map import ItineraryRouteMap
from desktop_client.components.slippy_map_canvas import SlippyMapCanvas
from desktop_client.components.place_card import PlaceCard
from desktop_client.components.stop_card import StopCard
from desktop_client.components.dialogs import (
    show_place_detail_dialog,
    show_custom_venue_dialog,
    show_edit_stop_dialog,
    show_export_dialog,
    show_confirm_dialog,
)

__all__ = [
    "BottomTabBar",
    "OfflineHostBanner",
    "SplashOverlay",
    "WorkflowHeader",
    "ItineraryRouteMap",
    "SlippyMapCanvas",
    "PlaceCard",
    "StopCard",
    "show_place_detail_dialog",
    "show_custom_venue_dialog",
    "show_edit_stop_dialog",
    "show_export_dialog",
    "show_confirm_dialog",
]
