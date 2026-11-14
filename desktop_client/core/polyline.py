"""Polyline Encoding, Decoding, Haversine Distance, and Route Spline Utilities.

Ported from Project/src/app/core/utils/polyline.util.ts.
Implements Google Encoded Polyline Algorithm (precision 5), Haversine metrics,
geodesic spline interpolation for offline previews, and multi-stop Google Maps URL generation.
"""

from __future__ import annotations
import math
from typing import Any, Optional, Sequence, Tuple
import urllib.parse


Coordinate = Tuple[float, float]  # (latitude, longitude)


def decode_polyline(encoded: str) -> list[Coordinate]:
    """Decodes a Google Encoded Polyline string into a list of (latitude, longitude) tuples."""
    if not encoded:
        return []

    points: list[Coordinate] = []
    index = 0
    length = len(encoded)
    lat = 0
    lng = 0

    while index < length:
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        points.append((lat / 1e5, lng / 1e5))

    return points


def encode_polyline(points: Sequence[Coordinate]) -> str:
    """Encodes a sequence of (latitude, longitude) tuples into Google Encoded Polyline format."""
    if not points:
        return ""

    result: list[str] = []
    prev_lat = 0
    prev_lng = 0

    for lat, lng in points:
        lat_int = round(lat * 1e5)
        lng_int = round(lng * 1e5)

        d_lat = lat_int - prev_lat
        d_lng = lng_int - prev_lng

        prev_lat = lat_int
        prev_lng = lng_int

        for d in (d_lat, d_lng):
            val = ~(d << 1) if d < 0 else (d << 1)
            while val >= 0x20:
                result.append(chr((0x20 | (val & 0x1F)) + 63))
                val >>= 5
            result.append(chr(val + 63))

    return "".join(result)


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates Great Circle distance between two coordinates in meters using the Haversine formula."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2) + (math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return r * c


def generate_geodesic_arc(
    start: Coordinate,
    end: Coordinate,
    points_count: int = 10,
    curvature: float = 0.06,
    num_points: Optional[int] = None,
) -> list[Coordinate]:
    """Generates a smooth quadratic Bezier arc between two coordinates for offline route preview."""
    if num_points is not None:
        points_count = num_points
    lat1, lng1 = start
    lat2, lng2 = end

    mid_lat = (lat1 + lat2) / 2.0
    mid_lng = (lng1 + lng2) / 2.0

    d_lat = lat2 - lat1
    d_lng = lng2 - lng1
    normal_lat = -d_lng * curvature
    normal_lng = d_lat * curvature

    control_lat = mid_lat + normal_lat
    control_lng = mid_lng + normal_lng

    points: list[Coordinate] = []
    for i in range(points_count + 1):
        t = i / float(points_count)
        one_minus_t = 1.0 - t
        lat = (one_minus_t * one_minus_t * lat1) + (2.0 * one_minus_t * t * control_lat) + (t * t * lat2)
        lng = (one_minus_t * one_minus_t * lng1) + (2.0 * one_minus_t * t * control_lng) + (t * t * lng2)
        points.append((lat, lng))

    return points


def build_google_maps_day_route_url(stops: Sequence[Any], travel_mode: str = "driving") -> Optional[str]:
    """Generates a multi-stop Google Maps directions URL for an ordered list of itinerary stops.

    Accepts ItineraryItem objects, Place objects, or coordinate dicts.
    """
    coords: list[Coordinate] = []

    for stop in stops:
        if stop is None:
            continue
        lat: Optional[float] = None
        lng: Optional[float] = None

        if isinstance(stop, dict):
            lat = stop.get("latitude") or (stop.get("place") or {}).get("latitude")
            lng = stop.get("longitude") or (stop.get("place") or {}).get("longitude")
        else:
            # Dataclass or Pydantic model
            place = getattr(stop, "place", None)
            if place is not None:
                lat = getattr(place, "latitude", None)
                lng = getattr(place, "longitude", None)
            if lat is None:
                lat = getattr(stop, "latitude", None)
                lng = getattr(stop, "longitude", None)

        if lat is not None and lng is not None and (-90.0 <= lat <= 90.0) and (-180.0 <= lng <= 180.0):
            coords.append((float(lat), float(lng)))

    if not coords:
        return None

    if len(coords) == 1:
        return f"https://www.google.com/maps/search/?api=1&query={coords[0][0]},{coords[0][1]}"

    origin = f"{coords[0][0]},{coords[0][1]}"
    destination = f"{coords[-1][0]},{coords[-1][1]}"

    base_url = (
        f"https://www.google.com/maps/dir/?api=1"
        f"&origin={origin}"
        f"&destination={destination}"
        f"&travelmode={urllib.parse.quote(travel_mode)}"
    )

    if len(coords) > 2:
        waypoint_strs = [f"{lat},{lng}" for lat, lng in coords[1:-1]]
        waypoints = urllib.parse.quote("|".join(waypoint_strs), safe="|")
        base_url += f"&waypoints={waypoints}"

    return base_url
