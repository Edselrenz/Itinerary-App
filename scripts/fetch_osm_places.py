#!/usr/bin/env python3
"""Queries Overpass API for all Nueva Ecija POIs and saves raw JSON."""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = DATA_DIR / "nueva_ecija_osm.json"

# Nueva Ecija bounding box: (south, west, north, east)
# 15.15, 120.70, 16.15, 121.40
BBOX = "15.15,120.70,16.15,121.40"

OVERPASS_QL = f"""[out:json][timeout:90];
(
  // Food & Dining
  node["amenity"~"cafe|restaurant|fast_food|food_court"]({BBOX});
  way["amenity"~"cafe|restaurant|fast_food|food_court"]({BBOX});

  // Lodging & Accommodations
  node["tourism"~"hotel|guest_house|motel|hostel|resort|chalet"]({BBOX});
  way["tourism"~"hotel|guest_house|motel|hostel|resort|chalet"]({BBOX});

  // Tourist Attractions & Culture
  node["tourism"~"attraction|viewpoint|museum|gallery"]({BBOX});
  way["tourism"~"attraction|viewpoint|museum|gallery"]({BBOX});
  node["historic"~"monument|memorial|ruins|heritage"]({BBOX});
  way["historic"~"monument|memorial|ruins|heritage"]({BBOX});
  node["amenity"~"arts_centre|community_centre|place_of_worship"]({BBOX});
  way["amenity"~"arts_centre|community_centre|place_of_worship"]({BBOX});

  // Nature, Parks & Recreation
  node["leisure"~"park|nature_reserve|garden|water_park|swimming_pool"]({BBOX});
  way["leisure"~"park|nature_reserve|garden|water_park|swimming_pool"]({BBOX});
  node["waterway"="waterfall"]({BBOX});
  node["natural"~"peak|spring"]({BBOX});

  // Shopping, Markets & Essentials
  node["shop"~"mall|supermarket|department_store|convenience"]({BBOX});
  way["shop"~"mall|supermarket|department_store|convenience"]({BBOX});
  node["amenity"~"marketplace|bank|pharmacy|hospital|clinic|fuel|bus_station"]({BBOX});
  way["amenity"~"marketplace|bank|pharmacy|hospital|clinic|fuel|bus_station"]({BBOX});
);
out center body;
"""

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

def fetch_overpass_data() -> dict:
    encoded_query = urllib.parse.urlencode({"data": OVERPASS_QL}).encode("utf-8")
    
    last_err = None
    for url in OVERPASS_ENDPOINTS:
        print(f"[INFO] Attempting Overpass fetch from {url}...")
        req = urllib.request.Request(
            url,
            data=encoded_query,
            headers={
                "User-Agent": "NuevaEcijaTravelItineraryApp/1.0 (contact: support@tripmo.ph)",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw_bytes = resp.read()
                data = json.loads(raw_bytes.decode("utf-8"))
                print(f"[SUCCESS] Received {len(data.get('elements', []))} elements from {url}")
                return data
        except Exception as e:
            print(f"[WARN] Failed fetching from {url}: {e}")
            last_err = e
            time.sleep(2)

    raise RuntimeError(f"All Overpass endpoints failed. Last error: {last_err}")

if __name__ == "__main__":
    data = fetch_overpass_data()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved raw OSM dataset to {OUTPUT_FILE}")

