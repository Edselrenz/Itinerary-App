"""Municipal transit hubs, tricycle fares, and Haversine leg commute guidance.

Ported from Project/src/app/core/data/commute-guide.data.ts for Desktop Parity.
"""

from dataclasses import dataclass
import math
from typing import Any, Optional


@dataclass
class CommuteInfo:
    transit_mode: str
    departure_hub: str
    drop_off_point: str
    estimated_travel_time: str
    estimated_fare: str
    travel_reminder: str


COMMUTE_BY_MUNICIPALITY: dict[str, CommuteInfo] = {
    "Bongabon": CommuteInfo(
        transit_mode="By Bus / UV Express",
        departure_hub="Cabanatuan City Central Terminal",
        drop_off_point="Ricky Food House / Bongabon Town Proper",
        estimated_travel_time="1 hr – 1 hr 30 mins",
        estimated_fare="₱66 – ₱80",
        travel_reminder="Tricycle transfer fares and UV Express schedules may vary by time of day. Morning departures (6:00 AM – 9:00 AM) run frequently.",
    ),
    "Pantabangan": CommuteInfo(
        transit_mode="By UV Express / Bus (Baler / Pantabangan route)",
        departure_hub="Cabanatuan City Central Terminal",
        drop_off_point="Pantabangan Junction / Lake Resort Crossing",
        estimated_travel_time="1 hr 30 mins – 2 hrs",
        estimated_fare="₱110 – ₱150",
        travel_reminder="Resorts around Lake Pantabangan and Highland Bali may require a local chartered tricycle or resort shuttle from the highway junction.",
    ),
    "General Tinio": CommuteInfo(
        transit_mode="By Jeepney / Tricycle",
        departure_hub="Gapan City Terminal or Cabanatuan Central Terminal",
        drop_off_point="General Tinio Municipal Hall / Minalungao Tourism Center",
        estimated_travel_time="1 hr – 1 hr 20 mins",
        estimated_fare="₱50 – ₱75",
        travel_reminder="Access to Minalungao National Park requires a local chartered tricycle from General Tinio poblacion. Standard local rates apply.",
    ),
    "Gapan City": CommuteInfo(
        transit_mode="By Bus (Five Star, Baliwag Transit) / Jeepney",
        departure_hub="Cabanatuan Central Terminal or Metro Manila Cubao/Pasay",
        drop_off_point="Gapan City Proper / Lumang Gapan Plaza",
        estimated_travel_time="30 mins – 45 mins from Cabanatuan",
        estimated_fare="₱40 – ₱60",
        travel_reminder="Walking distance to Tagpuan sa Lumang Gapan from the municipal plaza. Tricycles readily available at the national highway crossing.",
    ),
    "Science City of Muñoz": CommuteInfo(
        transit_mode="By Bus / Jeepney (San Jose route)",
        departure_hub="Cabanatuan City Central Terminal",
        drop_off_point="CLSU Main Gate / Muñoz Public Market",
        estimated_travel_time="45 mins – 1 hr",
        estimated_fare="₱50 – ₱70",
        travel_reminder="CLSU agricultural research centers, PCC carabao dairy center, and PhilRice are reachable via local campus tricycles.",
    ),
    "Cabanatuan City": CommuteInfo(
        transit_mode="By City Tricycle / Jeepney",
        departure_hub="Within Cabanatuan City",
        drop_off_point="Destination landmark / City Proper",
        estimated_travel_time="10 mins – 25 mins",
        estimated_fare="₱15 – ₱30",
        travel_reminder="Cabanatuan City serves as the primary transport gateway for Nueva Ecija with direct inter-provincial bus connections to Metro Manila and northern provinces.",
    ),
    "Gabaldon": CommuteInfo(
        transit_mode="By Bus / Van (Dingalan / Gabaldon line)",
        departure_hub="Cabanatuan City Central Terminal",
        drop_off_point="Gabaldon Poblacion / Dupinga Crossing",
        estimated_travel_time="1 hr 30 mins – 2 hrs",
        estimated_fare="₱90 – ₱120",
        travel_reminder="Dupinga River ecotourism site is accessible by tricycle from the town proper. Bring cash as ATMs are limited.",
    ),
    "San Jose City": CommuteInfo(
        transit_mode="By Bus / UV Express",
        departure_hub="Cabanatuan City Central Terminal",
        drop_off_point="San Jose City Public Market / Bus Stop",
        estimated_travel_time="1 hr – 1 hr 15 mins",
        estimated_fare="₱70 – ₱95",
        travel_reminder="Gateway to Northern Luzon. Major transit stop with frequent 24-hour bus services along Maharlika Highway.",
    ),
}


def get_commute_info_for_municipality(
    municipality_name: Optional[str] = None,
    place_name: Optional[str] = None,
) -> CommuteInfo:
    """Returns transit guidance and estimated fare for a given destination."""
    muni = (municipality_name or "").strip()
    if muni:
        for key, val in COMMUTE_BY_MUNICIPALITY.items():
            if muni.lower() in key.lower() or key.lower() in muni.lower():
                return val

    p_lower = (place_name or "").lower()
    if "minalungao" in p_lower:
        return COMMUTE_BY_MUNICIPALITY["General Tinio"]
    if "pantabangan" in p_lower or "highland bali" in p_lower or "casa batik" in p_lower:
        return COMMUTE_BY_MUNICIPALITY["Pantabangan"]
    if "lumang gapan" in p_lower:
        return COMMUTE_BY_MUNICIPALITY["Gapan City"]
    if any(k in p_lower for k in ["clsu", "philrice", "muñoz", "munoz", "carabao"]):
        return COMMUTE_BY_MUNICIPALITY["Science City of Muñoz"]
    if "bongabon" in p_lower or "rohi" in p_lower or "thornes" in p_lower:
        return COMMUTE_BY_MUNICIPALITY["Bongabon"]

    label = muni or "Nueva Ecija"
    return CommuteInfo(
        transit_mode="By Bus / Local UV Express",
        departure_hub="Cabanatuan City Central Terminal",
        drop_off_point=f"{label} Town Proper / Highway Crossing",
        estimated_travel_time="45 mins – 1 hr 30 mins",
        estimated_fare="₱50 – ₱100",
        travel_reminder="Provincial PUVs depart regularly from Cabanatuan Central Terminal. Check with local terminal marshals for schedule adjustments and night trips.",
    )


def calculate_haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Calculates Haversine distance in meters between two coordinates."""
    r = 6371000.0  # Earth radius in meters
    to_rad = math.radians
    d_lat = to_rad(lat2 - lat1)
    d_lon = to_rad(lon2 - lon1)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(to_rad(lat1)) * math.cos(to_rad(lat2)) * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return int(round(r * c))


@dataclass
class LegCommuteInfo(CommuteInfo):
    is_walking_distance: bool = False
    hop_distance_meters: Optional[int] = None
    hop_distance_km: float = 0.0

    @property
    def distance_km(self) -> float:
        return self.hop_distance_km

    @property
    def duration_mins(self) -> int:
        if self.estimated_travel_time:
            import re
            m = re.findall(r"\d+", self.estimated_travel_time)
            if m:
                return round(sum(int(x) for x in m) / len(m))
        return 15

    @property
    def display_text(self) -> str:
        icon = "🚶" if self.is_walking_distance else "🚗"
        dist = f"{self.hop_distance_km:.1f} km" if self.hop_distance_km >= 1.0 else f"{self.hop_distance_meters or round(self.hop_distance_km * 1000)} m"
        return f"{icon} {dist} • {self.estimated_travel_time} • {self.estimated_fare}"


def get_leg_commute_info(prev_stop: Any, curr_stop: Any) -> LegCommuteInfo:
    """Computes specific transit mode, travel time, and fare between consecutive stops."""
    # Extract attributes safely whether dataclass or dict
    def _get(obj: Any, key: str, fallback: Any = None) -> Any:
        if obj is None:
            return fallback
        if isinstance(obj, dict):
            return obj.get(key, fallback)
        return getattr(obj, key, fallback)

    curr_title = _get(curr_stop, "custom_title") or _get(_get(curr_stop, "place"), "name") or "Destination"
    curr_muni = _get(_get(curr_stop, "place"), "municipality_name") or "Nueva Ecija"

    if prev_stop is None:
        base = get_commute_info_for_municipality(curr_muni, curr_title)
        return LegCommuteInfo(
            transit_mode=base.transit_mode,
            departure_hub=base.departure_hub,
            drop_off_point=base.drop_off_point,
            estimated_travel_time=base.estimated_travel_time,
            estimated_fare=base.estimated_fare,
            travel_reminder=base.travel_reminder,
            is_walking_distance=False,
            hop_distance_meters=None,
            hop_distance_km=0.0,
        )

    prev_title = _get(prev_stop, "custom_title") or _get(_get(prev_stop, "place"), "name") or "Previous Stop"
    prev_muni = _get(_get(prev_stop, "place"), "municipality_name") or curr_muni

    # Calculate distance
    dist_meters = _get(curr_stop, "travel_distance_meters")
    if dist_meters is None:
        p_lat = _get(_get(prev_stop, "place"), "latitude") or _get(prev_stop, "custom_lat")
        p_lng = _get(_get(prev_stop, "place"), "longitude") or _get(prev_stop, "custom_lng")
        c_lat = _get(_get(curr_stop, "place"), "latitude") or _get(curr_stop, "custom_lat")
        c_lng = _get(_get(curr_stop, "place"), "longitude") or _get(curr_stop, "custom_lng")
        if p_lat and p_lng and c_lat and c_lng:
            dist_meters = calculate_haversine_meters(float(p_lat), float(p_lng), float(c_lat), float(c_lng))

    is_intra_town = str(prev_muni).lower().strip() == str(curr_muni).lower().strip()
    d_km = round(dist_meters / 1000.0, 1) if dist_meters is not None else 3.0

    # 1. Intra-town short walk (<= 1.2 km)
    if dist_meters is not None and dist_meters <= 1200:
        is_very_short = dist_meters <= 400
        return LegCommuteInfo(
            transit_mode="Walking" if is_very_short else "Walking or Short Tricycle Hop",
            departure_hub=prev_title,
            drop_off_point=curr_title,
            estimated_travel_time="3 – 5 mins walk" if is_very_short else f"{max(3, round(dist_meters / 80))} mins walk or 3 mins tricycle",
            estimated_fare="Free (Walking)" if is_very_short else "Free (Walk) or ₱15 – ₱25 tricycle",
            travel_reminder="Short distance within town proper. Walking is scenic and pleasant, or flag a passing tricycle.",
            is_walking_distance=True,
            hop_distance_meters=dist_meters,
            hop_distance_km=d_km,
        )

    # 2. Intra-town medium hop (> 1.2 km or < 5 km)
    if is_intra_town or (dist_meters is not None and dist_meters < 5000):
        mins_min = max(5, round((dist_meters or 3000) / 400))
        mins_max = max(10, round((dist_meters or 3000) / 250))
        return LegCommuteInfo(
            transit_mode="Local Tricycle",
            departure_hub=f"{prev_title} ({prev_muni})",
            drop_off_point=f"{curr_title} ({curr_muni})",
            estimated_travel_time=f"{mins_min} – {mins_max} mins",
            estimated_fare="₱25 – ₱50 per ride",
            travel_reminder=f"Intra-town transfer ({d_km} km). Local tricycles are readily stationed nearby or hailable along the road.",
            is_walking_distance=False,
            hop_distance_meters=dist_meters,
            hop_distance_km=d_km,
        )

    # 3. Inter-town corridor hop
    mins_min = max(20, round((dist_meters or 15000) / 700))
    mins_max = max(30, round((dist_meters or 15000) / 450))
    return LegCommuteInfo(
        transit_mode="Jeepney / UV Express / Inter-Town Bus",
        departure_hub=f"{prev_muni} Town Proper / Highway",
        drop_off_point=f"{curr_muni} Crossing / {curr_title}",
        estimated_travel_time=f"{mins_min} – {mins_max} mins",
        estimated_fare="₱35 – ₱85",
        travel_reminder=f"Inter-municipal corridor ({d_km} km from {prev_muni} to {curr_muni}). Ride passing PUVs, buses, or UV Express along Maharlika / provincial highways.",
        is_walking_distance=False,
        hop_distance_meters=dist_meters,
        hop_distance_km=d_km,
    )
